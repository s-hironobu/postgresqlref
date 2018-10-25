<pre>
typedef struct HeapTupleFields
{
        TransactionId t_xmin;           /* inserting xact ID */
        TransactionId t_xmax;           /* deleting or locking xact ID */

        union
        {
                CommandId       t_cid;          /* inserting or deleting command ID, or both */
                TransactionId t_xvac;   /* old-style VACUUM FULL xact ID */
        }                       t_field3;
} HeapTupleFields;

typedef struct DatumTupleFields
{
        int32           datum_len_;             /* varlena header (do not touch directly!) */

        int32           datum_typmod;   /* -1, or identifier of a record type */

        Oid                     datum_typeid;   /* composite type OID, or RECORDOID */

        /*                                                                                               
         * Note: field ordering is chosen with thought that Oid might someday                            
         * widen to 64 bits.                                                                             
         */
} DatumTupleFields;

typedef struct HeapTupleHeaderData
{
        union
        {
                HeapTupleFields t_heap;
                DatumTupleFields t_datum;
        }                       t_choice;

        ItemPointerData t_ctid;         /* current TID of this or newer tuple */

        /* Fields below here must match MinimalTupleData! */

        uint16          t_infomask2;    /* number of attributes + various flags */

        uint16          t_infomask;             /* various flag bits, see below */

        uint8           t_hoff;                 /* sizeof header incl. bitmap, padding */

        /* ^ - 23 bytes - ^ */

        bits8           t_bits[1];              /* bitmap of NULLs -- VARIABLE LENGTH */

        /* MORE DATA FOLLOWS AT END OF STRUCT */
} HeapTupleHeaderData;

typedef HeapTupleHeaderData *HeapTupleHeader;


</pre>