<pre>
typedef struct XLogRecord
{
    pg_crc32        xl_crc;    /* 後継のデータのCRC誤り訂正コード */
    XLogRecPtr      xl_prev;   /* 直前のXLOGアドレス */
    TransactionId xl_xid;      /* トランザクションID */
    uint32          xl_tot_len;/* このトランザクションのデータ長 */
    uint32          xl_len;    /* このログレコードの長さ */
    uint8           xl_info;   /* RMの操作コード */
    RmgrId          xl_rmid;   /* どのRMが書き込んだか */
} XLogRecord;

</pre>
