var url = "https://shcutq.gq/"

async function user_reg() {
    let res = await fetch(url + 'reg', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            login: $("#reg_login").val(),
            password: sha256($("#reg_password").val()),
            email: $("#reg_email").val(),
            first_name: $("#reg_name").val(),
            last_name: $("#reg_surname").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $.cookie("error", 0, {expires: 0})
            $(".error").hide();
            $(".success").show();
            setTimeout(() => document.location.href = "login.html", 3000);
        }
        if (data.code !== 1000) {
            $.cookie('error', 1300)
            document.location.href = "reg.html";
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

if ($.cookie("error") !== undefined) {
    $(".error").show();
}