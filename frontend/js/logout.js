function logout() {
    $.removeCookie('token');
    document.location.href = 'index.html';
}