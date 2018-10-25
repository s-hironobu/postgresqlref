<!----------------------------- 以下は印刷不要。WEB向け ------------------------------------------------->

<pre>
src/include/storage/bufpage.h
typedef struct PageHeaderData
{
        /* XXX LSN is member of *any* block, not only page-organized ones */
        XLogRecPtr      pd_lsn;         /* LSN: next byte after last byte of xlog
                                         * record for last change to this page */
        uint16          pd_tli;         /* least significant bits of the TimeLineID 
                                         * containing the LSN */
        uint16          pd_flags;       /* flag bits, see below */
        LocationIndex pd_lower;         /* offset to start of free space */
        LocationIndex pd_upper;         /* offset to end of free space */
        LocationIndex pd_special;       /* offset to start of special space */
        uint16          pd_pagesize_version;
        TransactionId pd_prune_xid;     /* oldest prunable XID, or zero if none */
        ItemIdData      pd_linp[1];     /* beginning of line pointer array */
} PageHeaderData;

typedef PageHeaderData *PageHeader;
</pre>
</div> 

<div id="layer_xlogrecptr" style="display: none;position:relative;margin-left:15pt" class="close">
<pre>
src/include/access/xlogdef.h

typedef struct XLogRecPtr
{
        uint32          xlogid;                 /* log file #, 0 based */
        uint32          xrecoff;                /* byte offset of location in log file */
} XLogRecPtr;
</pre>

<!--------------------------------------　ここまで印刷不要　---------------------------------------------->
