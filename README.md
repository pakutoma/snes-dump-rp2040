# snes-dumper-rp2040
##  概要
スーパーファミコンのROM吸い出し機の実験的な実装のソフトウェア部分です
I2Cバスの通信速度により非常に吸い出しが遅いです（0.7KB/sくらい）

## ハードウェアのパーツ
- RP2040を搭載したボード（Raspberry Pi Picoなど）
- MCP23017 * 2
- [I2Cバス用双方向電圧レベル変換モジュール](https://akizukidenshi.com/catalog/g/gM-05825/)
  - 要は3.3V(RP2040)の信号を5V(SNES)に変換できれば良いです
- 2.5mmピッチ62ピンソケット（SNES用）
  - Aliexpressとかで買うといいです
- 2.5mmピッチと2.54mmピッチを変換する何らかの手段
  - 作者はRE500というユニバーサル基板から手配線でフラットケーブルを引っ張ってMILコネクタで繋げました
  - このために基板を作るなら[cartreader](https://github.com/sanni/cartreader)を作ればいいと思います

## ピンアサイン
- MCP23017とのつなぎ方はrom_interface.pyを参考にしてください
  - 片方のMCP23017にA15-A0を接続
  - もう片方のMCP23017にA23-A16と、D7-D0を接続
- 他のピンは[適当に](https://snes.nesdev.org/wiki/Cartridge_connector)5VかGNDにつなげてください
  - /WRと/RESETと電源を5V, ほかはGNDにするといいと思います

## 使い方
1. ボードにclientの中身を書き込む
2. host.pyを実行する
3. 数時間待つと吸い出される（かもしれない）

## 対応ROM
- LoROM
- HiROM

## 非対応ROM
- ExHiROM
- SA-1
- その他、動かないもの

## 利用ソフトウェア
- [MicroPython MCP23017 16-bit I/O Expander](https://github.com/mcauser/micropython-mcp23017)
  - client/mcp23017.py
  - MIT License

## 参考にしたもの
- [SNES Development Wiki](https://snes.nesdev.org/wiki/Main_Page)
  - [Cartridge connector](https://snes.nesdev.org/wiki/Cartridge_connector)
  - [Memory map](https://snes.nesdev.org/wiki/Memory_map)
  - [ROM header](https://snes.nesdev.org/wiki/ROM_header)

## ライセンス
Apache License 2.0