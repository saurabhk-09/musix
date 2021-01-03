var audio_list=document.getElementsByTagName("audio");
for (i=0;i<audio_list.length;i++)
{
    audio_list[i].addEventListener("play",function(event){
        for (i=0;i<audio_list.length;i++)
        {
            if(audio_list[i]!=event.target)
                audio_list[i].pause();
        }
    });
}


