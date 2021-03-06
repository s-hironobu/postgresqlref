# PostgreSQL全機能バイブル 原稿

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="クリエイティブ・コモンズ・ライセンス" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a>　＋　２条件

## 概要
これは書籍「<a href="https://www.amazon.co.jp/dp/4774153923">PostgreSQL全機能バイブル</a>」の原稿を多少アップデートしたものです。

数年前にアップデートを停止したので、多くの部分はまだversion 9.2対応です。しかし、前回の書籍化にあたって削除した部分を改めて取り込んだり、別途準備していた原稿をマージした部分もあります。

ライセンスは<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"></a><a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">クリエイティブ・コモンズ 表示 - 継承 4.0 国際 ライセンス</a>ベースです(２つ条件を追加しています)。詳細は本文書の末尾をご覧ください。

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

Headerファイルには目次が含まれています。もしも文書を追加するばあいにはHeaderファイルの目次部分にもリンクを追加する必要があります。また、節を入れ替えるなど、文書構成を変更する場合にもHeaderファイルの目次の変更が必要になります。

### html
生成されたHTMLファイル群があります。  ブラウザで文書をみるときにはこのディレクトリ以下のファイルを開いてください。

### Figures
OpenOfficeで作成した図表があります。

図表を原稿に反映させるには、反映させたい画像をキャプチャして適当な画像ファイル名にして、htmlディレクトリに保存します。

## ライセンス
基本的には<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"></a><a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">クリエイティブ・コモンズ 表示 - 継承 4.0 国際 ライセンス</a>の下に提供されているので、商用利用可能ですが、これに以下の２つの条件を追加します。これら２つはクリエイティブ・コモンズとは独立したものですが、クリエイティブ・コモンズ同様に継承されます。

### 題名
ISBNコード付きの書籍として書店で販売する場合、「PostgreSQL全機能バイブル」という名称をタイトルやサブタイトルなどに使わないでください。万が一使用しますと、書名の権利を有する出版社に提訴される可能性があります。

E-Bookや同人誌のような形態で販売する場合、「PostgreSQL全機能バイブル」というタイトルを使ってもかまいません。

なお、書籍以外での「PostgreSQL全機能バイブル」という名称の使用権は、私(鈴木啓修)が持っています。このため、書籍以外で使用する場合には一声かけていただければ、使用に際して反対はしません。

### 寄付
利益(売上ではありません)の一部の寄付をお願いします。これは強制ではありませんが元著者の意志を汲んでいただきたく存じます。

具体的には以下の２つの分野、および個人にそれぞれ利益の9%、8%、3%以上の寄付をお願いします。

#### 貧困対策分野
寄付団体などは指定しませんが、可能であれば貧困家庭で教育の機会を奪われている子供達に使われるようにしてください。

#### 動物愛護関係
活動実績などを吟味した上で、いくつか団体をリストアップする予定です。

#### 著作権管理者
現在の私の居住地の関係で著作権管理など実務を委託している人物に対して、管理費用の補填のために寄付をお願いします。詳細な事情については、具体化した際にご説明いたします。こちらに関しては、説明内容が納得できない場合には寄付をしない選択も可能です。

