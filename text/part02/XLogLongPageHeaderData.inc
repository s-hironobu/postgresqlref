<pre>

typedef XLogPageHeaderData *XLogPageHeader;

/*
 * When the XLP_LONG_HEADER flag is set, we store additional fields in the
 * page header.  (This is ordinarily done just in the first page of an
 * XLOG file.)  The additional fields serve to identify the file accurately.
 */
typedef struct XLogLongPageHeaderData
{
        XLogPageHeaderData std;         /* standard header fields */
        uint64          xlp_sysid;              /* system identifier from pg_control */
        uint32          xlp_seg_size;   /* just as a cross-check */
        uint32          xlp_xlog_blcksz;        /* just as a cross-check */
} XLogLongPageHeaderData;

</pre>