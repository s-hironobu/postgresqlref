<pre>
typedef struct BlockIdData
{
        uint16          bi_hi;
        uint16          bi_lo;
} BlockIdData;

typedef uint16 OffsetNumber;


typedef struct ItemPointerData
{
        BlockIdData ip_blkid;
        OffsetNumber ip_posid;
}

typedef struct RelFileNode
{
        Oid                     spcNode;                /* tablespace */
        Oid                     dbNode;                 /* database */
        Oid                     relNode;                /* relation */
} RelFileNode;

typedef struct xl_heaptid
{
        RelFileNode node;
        ItemPointerData tid;            /* changed tuple id */
} xl_heaptid;

typedef struct xl_heap_insert
{
        xl_heaptid      target;                 /* inserted tuple id */
        bool            all_visible_cleared;    /* PD_ALL_VISIBLE was cleared */
} xl_heap_insert;
</pre>
