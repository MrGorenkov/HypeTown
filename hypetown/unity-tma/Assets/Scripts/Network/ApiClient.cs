using UnityEngine;
using UnityEngine.Networking;
using System.Threading.Tasks;
using System;
using System.Text;
using System.Runtime.InteropServices;

/// <summary>
/// HTTP-клиент для связи Unity ↔ HYPETOWN Backend.
/// Авторизация через Telegram initData в заголовке.
/// </summary>
public class ApiClient : MonoBehaviour
{
    [Header("Backend")]
    [SerializeField] private string apiBaseUrl = "https://your-server.com";

    private string initData;

    // JS-интероп: получить initData из Telegram WebApp
    #if UNITY_WEBGL && !UNITY_EDITOR
    [DllImport("__Internal")]
    private static extern string GetTelegramInitData();
    #else
    private static string GetTelegramInitData() => "";
    #endif

    void Awake()
    {
        initData = GetTelegramInitData();
        if (string.IsNullOrEmpty(initData))
            Debug.LogWarning("[ApiClient] initData пуст — возможно, запущено не в TMA");
    }

    /// <summary>
    /// Загрузить полное состояние игрока с сервера.
    /// </summary>
    public async Task LoadGameState()
    {
        string json = await Get("/api/state");
        if (string.IsNullOrEmpty(json)) return;

        var response = JsonUtility.FromJson<GameStateResponse>(json);
        if (response?.player == null) return;

        var state = GameManager.Instance.Player;
        state.TgId = response.player.tg_id;
        state.Name = response.player.name;
        state.Avatar = response.player.avatar;
        state.Archetype = response.player.archetype;
        state.Level = response.player.level;
        state.XP = response.player.xp;
        state.Coins = response.player.coins;
        state.Stars = response.player.stars;
        state.TapPower = response.player.tap_power;
        state.PassiveIncome = response.player.passive_income;
        state.PvpRating = response.player.pvp_rating;
        state.ModelUrl = response.player.model_url;
        state.TonWallet = response.player.ton_wallet;

        Debug.Log($"[ApiClient] Состояние загружено: {state.Name}, coins={state.Coins}");
    }

    /// <summary>
    /// Отправить батч тапов на сервер.
    /// </summary>
    public async Task SendTaps(int tapCount)
    {
        string body = JsonUtility.ToJson(new TapRequest { taps = tapCount });
        string json = await Post("/api/tap", body);
        if (string.IsNullOrEmpty(json)) return;

        var response = JsonUtility.FromJson<TapResponse>(json);
        // Синхронизация серверного значения
        GameManager.Instance.Player.Coins = response.total_coins;
        GameManager.Instance.UIManager.UpdateCoins(response.total_coins);
    }

    /// <summary>
    /// Обновить URL 3D-модели.
    /// </summary>
    public async Task UpdateModelUrl(string modelUrl)
    {
        string body = JsonUtility.ToJson(new ModelRequest { model_url = modelUrl });
        await Post("/api/model", body);
    }

    /// <summary>
    /// Привязать TON-кошелёк.
    /// </summary>
    public async Task ConnectWallet(string address)
    {
        string body = JsonUtility.ToJson(new WalletRequest { address = address });
        await Post("/api/wallet/connect", body);
    }

    // ── HTTP-хелперы ────────────────────────────────────────────────

    async Task<string> Get(string endpoint)
    {
        using var request = UnityWebRequest.Get(apiBaseUrl + endpoint);
        request.SetRequestHeader("Authorization", initData);
        var op = request.SendWebRequest();
        while (!op.isDone) await Task.Yield();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[ApiClient] GET {endpoint}: {request.error}");
            return null;
        }
        return request.downloadHandler.text;
    }

    async Task<string> Post(string endpoint, string jsonBody)
    {
        byte[] bodyBytes = Encoding.UTF8.GetBytes(jsonBody);
        using var request = new UnityWebRequest(apiBaseUrl + endpoint, "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyBytes);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", initData);

        var op = request.SendWebRequest();
        while (!op.isDone) await Task.Yield();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[ApiClient] POST {endpoint}: {request.error}");
            return null;
        }
        return request.downloadHandler.text;
    }
}

// ── JSON модели ─────────────────────────────────────────────────────

[Serializable]
public class GameStateResponse
{
    public PlayerData player;
    // buildings, upgrades — для расширения
}

[Serializable]
public class PlayerData
{
    public int tg_id;
    public string name;
    public string avatar;
    public string archetype;
    public int level;
    public long xp;
    public long coins;
    public int stars;
    public int tap_power;
    public int passive_income;
    public int pvp_rating;
    public string model_url;
    public string ton_wallet;
}

[Serializable]
public class TapRequest { public int taps; }

[Serializable]
public class TapResponse
{
    public long earned;
    public long total_coins;
    public int tap_power;
}

[Serializable]
public class ModelRequest { public string model_url; }

[Serializable]
public class WalletRequest { public string address; }
