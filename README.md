## Moosic, the Discord Music Bot
![Maui](https://i.imgur.com/tTb9v2X_d.webp?maxwidth=760&fidelity=grand)

This bot responds to user commands in a Discord text channel, joining the user's voice channel and playing songs. 
The bot uses youtube-dl to search songs from YouTube, streaming the audio into the user's voice channel.
A queue system is implemented, being able to queue multiple songs from multiple users and playing them one after another. 
The queue currently is not auto-looping, meaning after a song is played, it will not be re-added to the end of the queue unless toggled.

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
!remove <index>, remove the <index>'th song in the queue
!loop, toggles the auto-looping feature
```

## To-Do
 - [x] Reformat !np output to include song duration and YouTube link as an embed
 - [x] Reformat !q output to be an embed with a numbered list of all songs in queue (with song duration and YouTube link)
 - [ ] Add loop toggle
 - [ ] Allow Spotify links
 - [x] Allow removing of specific songs in the queue (by index)
 - [ ] Add guess the song game
