function reload_ui_profile(profile_name){
    document.body.innerHTML='<h1 style="font-family:monospace;margin-top:20%;color:lightgray;text-align:center;">Loading ' + profile_name + ' ...</h1>';
    setTimeout(function(){location.reload()},3500)

    return profile_name
}