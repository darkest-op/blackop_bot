//+------------------------------------------------------------------+
//| BLACKOP GOLD EA - v0.1                                           |
//| XAUUSD EMA/RSI prototype for MT5                                 |
//| DEMO-ONLY. Trading disabled by default.                          |
//+------------------------------------------------------------------+
#property strict
#property version   "0.10"
#property description "BLACKOP GOLD demo-only XAUUSD research prototype"

#include <Trade/Trade.mqh>
CTrade trade;

input bool   EnableTrading       = false; // Keep false until demo testing is complete
input double RiskPercent         = 0.25;  // Prototype risk budget per trade
input int    FastEMA             = 50;
input int    SlowEMA             = 200;
input int    RSIPeriod           = 14;
input int    ATRPeriod           = 14;
input double StopATR             = 2.0;
input double TargetATR           = 3.0;
input int    MaxSpreadPoints     = 0;     // 0 disables spread filter; configure per broker
input ulong  MagicNumber         = 261122;

int fastHandle = INVALID_HANDLE;
int slowHandle = INVALID_HANDLE;
int rsiHandle  = INVALID_HANDLE;
int atrHandle  = INVALID_HANDLE;
datetime lastBar = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   // Hard safety lock: this prototype refuses to initialize on live accounts.
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
   {
      Print("BLACKOP: live/non-demo account detected. EA initialization refused.");
      return INIT_FAILED;
   }

   // Accept broker suffixes such as XAUUSDm, but not unrelated symbols.
   if(StringFind(_Symbol, "XAUUSD") < 0)
   {
      Print("BLACKOP: attach this EA to an XAUUSD symbol. Current: ", _Symbol);
      return INIT_FAILED;
   }

   if(RiskPercent <= 0.0 || RiskPercent > 1.0 ||
      FastEMA <= 0 || SlowEMA <= FastEMA ||
      RSIPeriod <= 0 || ATRPeriod <= 0 ||
      StopATR <= 0.0 || TargetATR <= 0.0)
   {
      Print("BLACKOP: invalid inputs. RiskPercent must be >0 and <=1.");
      return INIT_PARAMETERS_INCORRECT;
   }

   fastHandle = iMA(_Symbol, PERIOD_M15, FastEMA, 0, MODE_EMA, PRICE_CLOSE);
   slowHandle = iMA(_Symbol, PERIOD_M15, SlowEMA, 0, MODE_EMA, PRICE_CLOSE);
   rsiHandle  = iRSI(_Symbol, PERIOD_M15, RSIPeriod, PRICE_CLOSE);
   atrHandle  = iATR(_Symbol, PERIOD_M15, ATRPeriod);

   if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE ||
      rsiHandle == INVALID_HANDLE || atrHandle == INVALID_HANDLE)
   {
      Print("BLACKOP: failed to create indicator handles. Error: ", GetLastError());
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(30);
   Print("BLACKOP GOLD v0.1 initialized on DEMO: ", _Symbol,
         ". EnableTrading=", EnableTrading);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(fastHandle != INVALID_HANDLE) IndicatorRelease(fastHandle);
   if(slowHandle != INVALID_HANDLE) IndicatorRelease(slowHandle);
   if(rsiHandle  != INVALID_HANDLE) IndicatorRelease(rsiHandle);
   if(atrHandle  != INVALID_HANDLE) IndicatorRelease(atrHandle);
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!EnableTrading)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_M15, 0);
   if(barTime == 0 || barTime == lastBar)
      return;
   lastBar = barTime;

   // Conservative: do not stack positions on the same gold symbol.
   if(PositionSelect(_Symbol))
      return;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.ask <= 0 || tick.bid <= 0)
      return;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0)
      return;

   if(MaxSpreadPoints > 0)
   {
      double spreadPoints = (tick.ask - tick.bid) / point;
      if(spreadPoints > MaxSpreadPoints)
         return;
   }

   double fast[], slow[], rsi[], atr[];
   ArrayResize(fast, 3);
   ArrayResize(slow, 3);
   ArrayResize(rsi, 3);
   ArrayResize(atr, 3);
   ArraySetAsSeries(fast, true);
   ArraySetAsSeries(slow, true);
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(atr, true);

   if(CopyBuffer(fastHandle, 0, 0, 3, fast) != 3 ||
      CopyBuffer(slowHandle, 0, 0, 3, slow) != 3 ||
      CopyBuffer(rsiHandle, 0, 0, 3, rsi) != 3 ||
      CopyBuffer(atrHandle, 0, 0, 3, atr) != 3)
      return;

   // Use completed candles only (bars 1 and 2).
   if(atr[1] <= 0)
      return;

   bool buySignal  = (fast[1] > slow[1] && rsi[2] <= 50.0 && rsi[1] > 50.0);
   bool sellSignal = (fast[1] < slow[1] && rsi[2] >= 50.0 && rsi[1] < 50.0);

   if(buySignal)
      OpenTrade(ORDER_TYPE_BUY, atr[1]);
   else if(sellSignal)
      OpenTrade(ORDER_TYPE_SELL, atr[1]);
}

//+------------------------------------------------------------------+
void OpenTrade(const ENUM_ORDER_TYPE orderType, const double atrValue)
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;

   double entry = (orderType == ORDER_TYPE_BUY) ? tick.ask : tick.bid;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   long stopsLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);

   if(entry <= 0 || point <= 0 || atrValue <= 0)
      return;

   double slDistance = atrValue * StopATR;
   double tpDistance = atrValue * TargetATR;
   double minimumDistance = (double)stopsLevel * point;

   if(slDistance < minimumDistance || tpDistance < minimumDistance)
   {
      Print("BLACKOP: broker minimum stop distance is larger than calculated SL/TP.");
      return;
   }

   double sl, tp;
   if(orderType == ORDER_TYPE_BUY)
   {
      sl = NormalizeDouble(entry - slDistance, digits);
      tp = NormalizeDouble(entry + tpDistance, digits);
   }
   else
   {
      sl = NormalizeDouble(entry + slDistance, digits);
      tp = NormalizeDouble(entry - tpDistance, digits);
   }

   double riskMoney = AccountInfoDouble(ACCOUNT_EQUITY) * RiskPercent / 100.0;
   double oneLotProfit = 0.0;

   if(riskMoney <= 0 ||
      !OrderCalcProfit(orderType, _Symbol, 1.0, entry, sl, oneLotProfit))
   {
      Print("BLACKOP: could not calculate estimated loss. Error: ", GetLastError());
      return;
   }

   double oneLotLoss = MathAbs(oneLotProfit);
   if(oneLotLoss <= 0)
      return;

   double rawVolume = riskMoney / oneLotLoss;
   double minVolume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxVolume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double volumeStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(volumeStep <= 0 || minVolume <= 0 || rawVolume < minVolume)
   {
      Print("BLACKOP: trade skipped. Broker minimum lot would exceed the risk budget.");
      return;
   }

   double volume = MathFloor(rawVolume / volumeStep) * volumeStep;
   volume = MathMin(volume, maxVolume);
   volume = NormalizeDouble(volume, 8);

   if(volume < minVolume)
      return;

   bool sent = false;
   if(orderType == ORDER_TYPE_BUY)
      sent = trade.Buy(volume, _Symbol, 0.0, sl, tp, "BLACKOP demo BUY");
   else
      sent = trade.Sell(volume, _Symbol, 0.0, sl, tp, "BLACKOP demo SELL");

   if(!sent)
      Print("BLACKOP: order rejected: ", trade.ResultRetcodeDescription());
   else
      Print("BLACKOP: demo order submitted. Volume=", volume,
            " SL=", sl, " TP=", tp);
}
//+------------------------------------------------------------------+
