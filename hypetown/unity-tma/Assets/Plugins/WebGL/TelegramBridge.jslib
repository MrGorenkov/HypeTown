mergeInto(LibraryManager.library, {
    /**
     * Получить initData из Telegram WebApp для авторизации API-запросов.
     * Вызывается из C# через [DllImport("__Internal")].
     */
    GetTelegramInitData: function () {
        var initData = "";
        if (window.Telegram && window.Telegram.WebApp) {
            initData = window.Telegram.WebApp.initData || "";
        }
        var bufferSize = lengthBytesUTF8(initData) + 1;
        var buffer = _malloc(bufferSize);
        stringToUTF8(initData, buffer, bufferSize);
        return buffer;
    },

    /**
     * Вызвать Telegram HapticFeedback при тапе.
     */
    TriggerHapticFeedback: function () {
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
            window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
        }
    },

    /**
     * Развернуть Mini App на весь экран.
     */
    ExpandWebApp: function () {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.expand();
        }
    },

    /**
     * Закрыть Mini App.
     */
    CloseWebApp: function () {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.close();
        }
    }
});
