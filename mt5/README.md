# BLACKOP GOLD — MT5 prototype

This folder contains the first MQL5 Expert Advisor prototype for XAUUSD.

## Safety status

- **Demo accounts only:** the EA refuses to initialize on a live/non-demo account.
- **Trading disabled by default:** `EnableTrading=false`. Do not enable it until it has been compiled, inspected, and tested in the MT5 Strategy Tester and on a demo account.
- This is an experimental EMA(50/200) + RSI(14) + ATR strategy, not a proven profitable system.
- It has not yet been validated against HFM or Weltrade contract specifications, execution rules, spreads, slippage, swaps, or minimum lot sizes.
- The risk calculation is an estimate using MT5's `OrderCalcProfit`; gaps, slippage, commissions, and execution conditions can make actual losses larger.
- No live-trading use is approved. A $10–$20 balance is especially vulnerable to minimum-volume and spread constraints.

## Strategy prototype

- Symbol: broker's XAUUSD symbol (suffixes such as XAUUSDm are accepted)
- Timeframe: M15
- Trend filter: EMA 50 versus EMA 200
- Entry: RSI crosses the 50 level in the direction of the EMA trend
- SL/TP: 2.0 ATR / 3.0 ATR
- Position sizing: 0.25% of equity risk budget, with a trade skipped if broker minimum volume exceeds the estimate
- One position per symbol at a time

## Compile and test

1. Open MetaTrader 5 **desktop** on a Windows computer or a Windows VPS. The iPhone MT5 app cannot compile or run Expert Advisors.
2. Open MetaEditor, create/open an Expert Advisor, and place `BLACKOP_GOLD_EA.mq5` in `MQL5/Experts`.
3. Compile and resolve any compiler warnings/errors before testing.
4. In Strategy Tester, select the broker's XAUUSD symbol, Every tick based on real ticks if available, and M15.
5. Keep `EnableTrading=false` for initial compilation. For a controlled demo test only, set it to true in the tester/demo environment.
6. Forward-test on demo and inspect trade logs, drawdown, spread sensitivity, and actual volume calculations.

## Telegram's role

Telegram can deliver alerts and receive safe status/notification messages. It does not run MT5, host this EA, increase an AI provider's API quota, or directly execute broker trades. The existing repository's Telegram signal workflows are separate from this MT5 Expert Advisor.

## Next engineering tasks

- Compile and test the EA in MetaEditor/Strategy Tester.
- Verify HFM and Weltrade XAUUSD contract specifications and symbol names.
- Add daily loss limits, maximum trades per day, trading-session filters, and a robust kill switch.
- Design a secure MT5-to-Telegram notification bridge only after the EA is validated.

**No profit guarantee. Do not deploy on a live account.**
