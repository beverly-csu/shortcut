var url = "https://shcutq.gq/"

async function user_auth() {
    let res = await fetch(url + 'user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            login: $("#auth_login").val(),
            password: sha256($("#auth_password").val())
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $.cookie("token", data.token, {domain: "shcut.gq"});
            $.cookie("error", 0, {expires: 0})
            $(".error").hide();
            $(".success").show();
            setTimeout(() => document.location.href = "index.html", 3000);
        }
        if (data.code !== 1000) {
            $.cookie('error', 1300)
            document.location.href = "login.html";
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

if ($.cookie("error") !== undefined) {
    $(".error").show();
}