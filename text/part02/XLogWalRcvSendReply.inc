<pre>
XLogWalRcvSendReply(void)@src/backend/replication/walreceiver.c
 /* Construct a new message */
 reply_message.write = LogstreamResult.Write;
 reply_message.flush = LogstreamResult.Flush;
 reply_message.apply = GetXLogReplayRecPtr();
 reply_message.sendTime = now;

 /* Prepend with the message type and send it. */
 buf[0] = 'r';
 memcpy(&buf[1], &reply_message, sizeof(StandbyReplyMessage));
 walrcv_send(buf, sizeof(StandbyReplyMessage) + 1);
</pre>
