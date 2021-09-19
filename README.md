## Moosic, the Discord Music Bot
![Maui](C:\Users\zyxan\Desktop\PICS)

This bot responds to user commands in a Discord text channel, joining the user's voice channel and playing songs. 
The bot uses youtube-dl to search songs from YouTube, streaming the audio into the user's voice channel.
A queue system is implemented, being able to queue multiple songs from multiple users and playing them one after another. 
The queue currently is auto-looping, meaning after a song is played, it will be re-added to the end of the queue.

### The following commands can be used:
```
!p <name/url>, searches youtube for <name/url> and plays the first item, joining the user's voice channel if not already in it
!join, joins the user's voice channel
!die, leaves the current voice channel
!yw, joins the user's voice channel and plays Dwayne Johnson's You're Welcome from Moana
!ty, sends a Discord embed message in the user's text channel (you're welcome!!)
!pause, pauses the currently playing song
!resume, resumes the currently playing song
!np, (short for now playing) shows the currently playing song
!q, shows all the songs in the queue
!clear, removes all the songs in the queue
!fs, (short for force skip) skips the currently playing song
```

## To-Do
 - Allow Spotify links and possibly switch from YouTube to Spotify as the song source
 - Allow removing of specific songs in the queue (by index)
 - Reformat !np output to include song duration and YouTube link as an embed
 - Reformat !q output to be an embed with a numbered list of all songs in queue (with song duration and YouTube link)
