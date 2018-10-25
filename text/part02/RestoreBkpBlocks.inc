<p>
参照：RestoreBkpBlocks()@src/backend/access/transam/xlog.cのコメント
</p>

<pre>

/*
 * Restore the backup blocks present in an XLOG record, if any.
 *
 * We assume all of the record has been read into memory at *record.
 *
 * Note: when a backup block is available in XLOG, we restore it
 * unconditionally, even if the page in the database appears newer.
 * This is to protect ourselves against database pages that were partially
 * or incorrectly written during a crash.  We assume that the XLOG data
 * must be good because it has passed a CRC check, while the database 
 * page might not be.  This will force us to replay all subsequent
 * modifications of the page that appear in XLOG, rather than possibly
 * ignoring them as already applied, but that's not a huge drawback.
 *
 * If 'cleanup' is true, a cleanup lock is used when restoring blocks.
 * Otherwise, a normal exclusive lock is used.  During crash recovery, that's 
 * just pro forma because there can't be any regular backends in the system,
 * but in hot standby mode the distinction is important. The 'cleanup'
 * argument applies to all backup blocks in the WAL record, that suffices for
 * now.
 */
void
RestoreBkpBlocks(XLogRecPtr lsn, XLogRecord *record, bool cleanup)
</pre>