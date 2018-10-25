
<pre>
<source>
typedef struct XLogPageHeaderData
{
        uint16          xlp_magic;     /* WALのマジックナンバー */
        uint16          xlp_info;      /* flag bits, see below */
        TimeLineID      xlp_tli;       /* TimeLineID */
        XLogRecPtr      xlp_pageaddr;  /* このページのXLOGアドレス = LSN */
} XLogPageHeaderData;
</source>
</pre>

<p>
重要な項目のみ説明する。
</p>

<p>
WALのマジックナンバーはPostgreSQLのバージョン毎に異なり、ver9.1は0xd066、ver9.0は0xd064、ver8.4は0xd063である。
TimeLineIDは[<2-XX>]で説明する。
次のxlp_pageaddrはそのページの先頭番地を表すLSNが書き込まれている。
</p>

<p>
ファイル名の命名規則から判るように、
LSNを指定すれば、それがWALログセグメントファイルのどのアドレスに対応するかすぐに計算できる。
あえてページ毎にそのページのLSNを記録するのは、マイルストーンのようなものと理解すればよい。
</p>
