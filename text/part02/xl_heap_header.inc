
<p>
We don't store the whole fixed part (HeapTupleHeaderData) of an inserted or updated tuple in WAL;
<br>
 we can save a few bytes by reconstructing the fields that are available elsewhere in the WAL record, 
or perhaps just  plain needn't be reconstructed.  
<br>
These are the fields we must store.
<br>
<br>
 NOTE: t_hoff could be recomputed, but we may as well store it because it will come for free due to alignment considerations.

</p>
