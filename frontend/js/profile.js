var url = "https://shcutq.gq/"

async function user_profile() {
    let res = await fetch(url + 'user', {
        method: 'GET',
        headers: {
            "Authorization": "Bearer " + $.cookie('token')
        },
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $("#user-login").text(data.full_name);
            $("#profileLogin").text(data.login);
            $("#profileEmail").text(data.email);
            $("#profileFullName").text(data.full_name);
            $("#profileDate").text(data.date_reg);
        } else {
            document.location.href = "login.html";
            $.cookie("token", "", {expires: 0});
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function user_delete() {
    let res = await fetch(url + 'user', {
        method: 'DELETE',
        headers: {
            "Authorization": "Bearer " + $.cookie('token')
        },
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            document.location.href = "login.html";
            $.cookie("token", "", {expires: 0});
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

user_profile().then();