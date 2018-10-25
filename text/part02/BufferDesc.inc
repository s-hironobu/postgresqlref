
<pre>
/*
 * Flags for buffer descriptors
 *
 * Note: TAG_VALID essentially means that there is a buffer hashtable
 * entry associated with the buffer's tag.
 */
#define BM_DIRTY                                (1 << 0)                /* data needs writing */
#define BM_VALID                                (1 << 1)                /* data is valid */
#define BM_TAG_VALID                    (1 << 2)                /* tag is assigned */
#define BM_IO_IN_PROGRESS               (1 << 3)                /* read or write in progress */
#define BM_IO_ERROR                             (1 << 4)                /* previous I/O failed */
#define BM_JUST_DIRTIED                 (1 << 5)                /* dirtied since write started */
#define BM_PIN_COUNT_WAITER             (1 << 6)                /* have waiter for sole pin */
#define BM_CHECKPOINT_NEEDED    (1 << 7)                /* must write for checkpoint */
#define BM_PERMANENT                    (1 << 8)                /* permanent relation (not unlogged) */


src/include/storage/buf_internals.h
typedef struct sbufdesc
{
   BufferTag    tag;                 /* ID of page contained in buffer */
   BufFlags     flags;               /* see bit definitions above */
   uint16       usage_count;         /* usage counter for clock sweep code */
   unsigned     refcount;            /* # of backends holding pins on buffer */
   int          wait_backend_pid;    /* backend PID of pin-count waiter */
   slock_t      buf_hdr_lock;        /* protects the above fields */
   int          buf_id;              /* buffer's index number (from 0) */
   int          freeNext;            /* link in freelist chain */

   LWLockId     io_in_progress_lock; /* to wait for I/O to complete */
   LWLockId     content_lock;        /* to lock access to buffer contents */
} BufferDesc;
</pre>

