<pre>
typedef struct CheckPoint
{
        XLogRecPtr      redo;                   /* next RecPtr available when we began to
                                                 * create CheckPoint (i.e. REDO start point) */
        TimeLineID      ThisTimeLineID; /* current TLI */
        uint32          nextXidEpoch;   /* higher-order bits of nextXid */
        TransactionId nextXid;          /* next free XID */
        Oid                     nextOid;                /* next free OID */
        MultiXactId nextMulti;          /* next free MultiXactId */
        MultiXactOffset nextMultiOffset;        /* next free MultiXact offset */
        TransactionId oldestXid;        /* cluster-wide minimum datfrozenxid */
        Oid                     oldestXidDB;    /* database with minimum datfrozenxid */
        pg_time_t       time;                   /* time stamp of checkpoint */

        /*
         * Oldest XID still running. This is only needed to initialize hot standby
         * mode from an online checkpoint, so we only bother calculating this for
         * online checkpoints and only when wal_level is hot_standby. Otherwise
         * it's set to InvalidTransactionId.
         */
        TransactionId oldestActiveXid;
} CheckPoint;
</pre>
