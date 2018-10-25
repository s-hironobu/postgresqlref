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


typedef struct xl_heap_update
{
        xl_heaptid      target;                 /* deleted tuple id */
        ItemPointerData newtid;         /* new inserted tuple id */
        bool            all_visible_cleared;    /* PD_ALL_VISIBLE was cleared */
        bool            new_all_visible_cleared;                /* same for the page of newtid */
} xl_heap_update;
</pre>
