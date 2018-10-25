<p>
gccのコンパイルオプションにマクロ"OPTIMIZER_DEBUG"を設定してPostgreSQLを再インストールすると、
列挙された問い合わせ計画がすべて標準出力できる。
<br>
具体例を示す。
</p>

<pre>
SELECT * FROM tb1, tb2 WHERE tb1.b = tb2.b; 
</pre>

<p>
[レベル１]
<blockquote>
テーブル毎に最小コストのパスを求める。
</p>

<table><tr>

<td>
(1)テーブルtb1の問い合わせ計画
<pre>
RELOPTINFO (1): rows=9 width=8
	joininfo: tb1.b = tb2.b
	path list:
	SeqScan(1) rows=9 cost=0.00..1.09

	cheapest startup path:
	SeqScan(1) rows=9 cost=0.00..1.09

	cheapest total path:
	SeqScan(1) rows=9 cost=0.00..1.09
</pre>

</td><td>

(2)テーブルtb2の問い合わせ計画
<pre>
RELOPTINFO (2): rows=8 width=8
	joininfo: tb1.b = tb2.b
	path list:
	SeqScan(2) rows=8 cost=0.00..1.08

	cheapest startup path:
	SeqScan(2) rows=8 cost=0.00..1.08

	cheapest total path:
	SeqScan(2) rows=8 cost=0.00..1.08
</pre>

</td>
</tr></table>

</blockquote>


<p>
[レベル2]
<blockquote>
レベル1の結果をもとに、テーブルの結合方式毎のコストを推定し、最小コストのパスを選ぶ。
</p>

<pre>
RELOPTINFO (1 2): rows=8 width=8
	path list:
	HashJoin(1 2) rows=8 cost=1.10..2.32
	  clauses: tb1.b = tb2.b
		SeqScan(1) rows=9 cost=0.00..1.09
		SeqScan(2) rows=8 cost=0.00..1.08
	NestLoop(1 2) rows=8 cost=1.09..3.80
	  clauses: tb1.b = tb2.b
		SeqScan(1) rows=9 cost=0.00..1.09
		Material(2) rows=8 cost=1.09..1.17
			SeqScan(2) rows=8 cost=0.00..1.08
	NestLoop(1 2) rows=8 cost=0.00..10.70
	  clauses: tb1.b = tb2.b
		SeqScan(2) rows=8 cost=0.00..1.08
		SeqScan(1) rows=9 cost=0.00..1.09

	cheapest startup path:
	NestLoop(1 2) rows=8 cost=0.00..10.70
	  clauses: tb1.b = tb2.b
		SeqScan(2) rows=8 cost=0.00..1.08
		SeqScan(1) rows=9 cost=0.00..1.09

	cheapest total path:
	HashJoin(1 2) rows=8 cost=1.10..2.32
	  clauses: tb1.b = tb2.b
		SeqScan(1) rows=9 cost=0.00..1.09
		SeqScan(2) rows=8 cost=0.00..1.08
</pre>

</blockquote>

<p>
オプティマイザは列挙された3つの問い合わせ計画のうち、ハッシュ結合のコスト(2.32)と
入れ子反復結合のコスト(3.80と10.70)を比較し、ハッシュ結合を選択する。
</p>
