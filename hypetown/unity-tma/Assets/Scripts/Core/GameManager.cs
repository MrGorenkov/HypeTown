using UnityEngine;
using System;

/// <summary>
/// Главный менеджер игры: инициализация, состояние, связь между системами.
/// Синглтон — живёт всю сессию.
/// </summary>
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [Header("Состояние игрока")]
    public PlayerState Player;

    [Header("Ссылки на менеджеры")]
    public TapManager TapManager;
    public CharacterLoader CharacterLoader;
    public UIManager UIManager;
    public ApiClient ApiClient;

    public event Action<long> OnCoinsChanged;
    public event Action<int> OnTapPowerChanged;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    async void Start()
    {
        // Загрузка состояния с сервера
        await ApiClient.LoadGameState();

        // Загрузка 3D-модели персонажа
        if (!string.IsNullOrEmpty(Player.ModelUrl))
        {
            await CharacterLoader.LoadCharacterModel(Player.ModelUrl);
        }
        else
        {
            CharacterLoader.LoadDefaultModel(Player.Archetype);
        }

        UIManager.UpdateAll();
    }

    public void AddCoins(long amount)
    {
        Player.Coins += amount;
        OnCoinsChanged?.Invoke(Player.Coins);
        UIManager.UpdateCoins(Player.Coins);
    }
}

/// <summary>
/// Данные игрока, синхронизируемые с сервером.
/// </summary>
[Serializable]
public class PlayerState
{
    public int TgId;
    public string Name;
    public string Avatar;
    public string Archetype;
    public int Level;
    public long XP;
    public long Coins;
    public int Stars;
    public int TapPower = 1;
    public int PassiveIncome;
    public int PvpRating;
    public string ModelUrl;
    public string TonWallet;
}
