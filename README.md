# 自分用PostgreSQLマニュアル a.k.a. PostgreSQL全機能バイブル 原稿


## 概要
これは書籍「<a href="https://www.amazon.co.jp/dp/4774153923">PostgreSQL全機能バイブル</a>」の原稿を、自分用のリファレンスとしてアップデート・リライトしたものです。
しかし、まだ10％程度完了していない箇所があります。


内容はPostgreSQL version16対応(一部未対応)です。


自分用なので、自分がわかっていることについての解説は省略しています。よって、他人が読んでもわからない記述が多々あります。
また、自分が知らない事柄について、使う予定がない場合には調査や説明を省いています。


ライセンスについて。基本的にはこの文書の2次利用ができないように変更します。
以前のバージョン9.X対応の原稿はFinalBookVersionというブランチに保管してあります。


## 文書の作成
スクリプトmake.shを実行してください。htmlディレクトリ以下にHTMLファイルの文書が作成されます。

```
$ ./make.sh
```

## ディレクトリ構成

### text
パート毎に原稿があります。

原稿はHTMLをベースとした独自フォーマットで書かれています。独自フォーマットといっても基本的にはHTMLで、章や節などを設定するコマンドを追加しただけです。

### template
原稿をHTMLに変更する際に追加するヘッダーとフッターがあります。

Perlスクリプトrel.plは、ここにあるHeaderファイルとFooterファイルの内容を原稿の前後に追加します。

Headerファイルには目次が含まれています。もしも文書を追加する場合はHeaderファイルの目次部分にもリンクを追加する必要があります。
また、節を入れ替えるなど、文書構成を変更する場合にもHeaderファイルの目次の変更が必要になります。

### html
生成されたHTMLファイル群があります。  ブラウザで文書をみるときにはこのディレクトリ以下のファイルを開いてください。

### Figures
OpenOfficeで作成した図表があります。

図表を原稿に反映させるには、反映させたい画像をキャプチャして適当な画像ファイル名にして、htmlディレクトリに保存します。

## 説明が未完、もしくは理解が曖昧な箇所

- 3.02 initdb
       - sync-method
- 3-05 システムカタログ
	- 32システムカタログの説明
- 3-22 ロジカルレプリケーション
	- 運用関連の説明
- 4-06 パラメータ：レプリケーション
	- 11パラメータの説明
- 4-07 パラメータ：クエリ
	- enable_async_append, enable_material、enable_memoize、plan_cache_mode, recursive_worktable_factor
- 4-11 パラメータ：クライアント
	- vacuum関係の6パラメータの説明
- 6-04 CREATE TABLE
	- 13ストレージパラメータの説明
- 6-07 外部キー
	- INITIALLY IMMEDIATEの振る舞い
- 6-10 ALTER TABLE(1)
	- REPLICA IDENTITYについて
- 6-11 ALTER TABLE(2)
	- SET STORAGE,　SET attribute_option,　DROP EXPRESSIONについて
- 6-20 WINDOW句
	- EXCLUDE について
- 6-21 CTE
	- CYCLE句とSEARCH句
- 6-22 GROUP句
	- GROUPING SETS,　CUBE,　ROLLUP
- 6-28 FOR UPDATE and FOR SHARE
	- SKIP LOCKEDの説明
- 6-35 ALTER INDEX
	- 説明省略
- 6-38 TRIGGER
	- DEFERRABLE関連
- 6-46 VACUUM
	- DISABLE_PAGE_SKIPPINGとSKIP_LOCKEDの関係
- 6-53, 6-54 PUBLICATION and SUBSCRIPTION
	- 説明無し
- 7-31 スキーマ可視性照会関数
	- pg_statistics_obj_is_visible()
- 7-36 サーバシグナル送信関数
	- pg_log_backend_memory_contexts()
- 7-40 レプリケーション関数
	- 説明無し
- 7-42 インデックス保守関数
	- brinやginに関する4関数の説明
- 7-43 汎用ファイルアクセス関数
	- pg_ls_logicalmapdir()
- 7-46 統計情報関数
	- pg_mcv_list_items()


設定パラメータやSQLのオプションについて、上記以外にも理解が不十分なものが多々ある。


書籍化する場合には、不明な事柄についてはその都度ソースコードを調べたり、十分な調査を行った上で解説を書いていたが、
今回は自分用なので深い調査は行わず、公式ドキュメントの機械翻訳などをコピペしたり、
内容を深く理解せず単純に翻訳したものを記載している。


## ライセンス

2次利用はできません。完全に個人での利用のみです。会社やグループなど、あらゆる複数人数での利用もできません。
