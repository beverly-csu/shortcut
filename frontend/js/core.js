var url = "https://shcutq.gq/"

var myOffcanvas = document.getElementById('createLinkCanvas')
var bsOffcanvas = new bootstrap.Offcanvas(myOffcanvas)
var myOffcanvas1 = document.getElementById('updateLinkCanvas')
var bsOffcanvas1 = new bootstrap.Offcanvas(myOffcanvas1)

var linkTable = $("#userLinks").DataTable({
    "scrollX": true,
    "autoWidth": false,
    "language": {
        "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Russian.json"
    }
});

async function get_profile() {
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
        } else {
            document.location.href = "login.html";
            $.cookie("token", "", {expires: 0});
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

function chartUpdate(days, count){
    myChart.data.labels = days;
    myChart.data.datasets[0].data = count;
    myChart.update();
}

async function update_stats() {
    let res = await fetch(url + 'link_stats', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            link_id: $("#statsID").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            chartUpdate(data.date, data.redirects);
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function get_links() {
    let res = await fetch(url + 'get_links', {
        method: 'GET',
        headers: {
            "Authorization": "Bearer " + $.cookie('token')
        },
    });
    if (res.ok) {
        let data = await res.json();
        linkTable.clear();
        linkTable.rows.add(data.links);
        linkTable.draw();
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function get_link_info() {
    let res = await fetch(url + 'link_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            full_url: $("#createFullUrl").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $("#createShortUrl").val(data.short_url);
            $("#createTitle").val(data.title);
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function get_short_available() {
    let res = await fetch(url + 'available', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            short_url: $("#createShortUrl").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $("#createShortUrl").removeClass("busy");
            $("#createSubmit").prop("disabled", false);
        } else {
            $("#createShortUrl").addClass("busy");
            $("#createSubmit").prop("disabled", true);
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function create_link() {
    let res = await fetch(url + 'link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            full_url: $("#createFullUrl").val(),
            short_url: $("#createShortUrl").val(),
            access: $("#createAccess").val(),
            title: $("#createTitle").val(),
            secret_code: $("#createSecret").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            get_links().then();
            bsOffcanvas.hide();
            $("#createFullUrl").val("");
            $("#createShortUrl").val("");
            $("#createAccess").val("");
            $("#createTitle").val("");
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function update_info() {
    let res = await fetch(url + 'link?link_id=' + $("#updateID").val(), {
        method: 'GET',
        headers: {
            "Authorization": "Bearer " + $.cookie('token')
        }
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            $("#updateAccess").val(data.access);
            $("#updateFullUrl").val(data.full_url);
            $("#updateShortUrl").val(data.short_url);
            $("#updateTitle").val(data.title);
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function update_link(){
    let res = await fetch(url + 'link', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            link_id: $("#updateID").val(),
            short_url: $("#updateShortUrl").val(),
            full_url: $("#updateFullUrl").val(),
            access: $("#updateAccess").val()
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            get_links().then();
            bsOffcanvas1.hide();
            alert("Ссылка успешно обновлена");
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

async function delete_link() {
    let res = await fetch(url + 'link', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
        body: JSON.stringify({
            link_id: $("#deleteID").val(),
        })
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            get_links().then();
            alert("Ссылка успешно удалена");
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

$("#createFullUrl").focusout(function () {
    get_link_info().then();
})

$("#createShortUrl").focusout(function () {
    get_short_available().then();
})

get_links().then()
get_profile().then();

if ($.cookie("token") === undefined) {
    document.location.href = "login.html";
}