<pre>
typedef struct BkpBlock @ include/access/xlog_internal.h
{
        RelFileNode node;                       /* relation containing block */
        ForkNumber      fork;                   /* fork within the relation */
        BlockNumber block;                      /* block number */
        uint16          hole_offset;    /* number of bytes before "hole" */
        uint16          hole_length;    /* number of bytes in "hole" */

        /* ACTUAL BLOCK DATA FOLLOWS AT END OF STRUCT */
} BkpBlock;

</pre>

