function chartUpdate(days, count){
    if (days !== undefined) {
        allChart.data.labels = days;
        allChart.data.datasets[0].data = count;
        allChart.update();
    }
}

async function update_stats() {
    let res = await fetch(url + 'links_stats', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + $.cookie('token')
        },
    });
    if (res.ok) {
        let data = await res.json();
        if (data.code === 1000) {
            chartUpdate(data.date, data.redirects);
            $("#all_links").text("Количество ваших ссылок: " + data.links_count);
            $("#all_redirects").text("Количество переходов по всем вашим ссылкам: " + data.all_count);
        }
    } else {
        console.log("Ошибка HTTP: " + res.status);
    }
}

update_stats().then();