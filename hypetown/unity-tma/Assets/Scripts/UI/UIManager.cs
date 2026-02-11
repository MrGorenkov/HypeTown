using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Менеджер UI: отображение монет, уровня, floating text при тапе.
/// </summary>
public class UIManager : MonoBehaviour
{
    [Header("HUD")]
    [SerializeField] private TextMeshProUGUI coinsText;
    [SerializeField] private TextMeshProUGUI levelText;
    [SerializeField] private TextMeshProUGUI tapPowerText;
    [SerializeField] private TextMeshProUGUI nameText;
    [SerializeField] private Slider xpBar;

    [Header("Floating Text")]
    [SerializeField] private GameObject floatingTextPrefab;
    [SerializeField] private Canvas worldCanvas;

    [Header("Камера")]
    [SerializeField] private Camera mainCamera;

    void Start()
    {
        if (mainCamera == null)
            mainCamera = Camera.main;
    }

    public void UpdateAll()
    {
        var p = GameManager.Instance.Player;
        UpdateCoins(p.Coins);
        UpdateLevel(p.Level, p.XP);
        UpdateTapPower(p.TapPower);

        if (nameText != null)
            nameText.text = $"{p.Avatar} {p.Name}";
    }

    public void UpdateCoins(long coins)
    {
        if (coinsText != null)
            coinsText.text = FormatNumber(coins);
    }

    public void UpdateLevel(int level, long xp)
    {
        if (levelText != null)
            levelText.text = $"Ур. {level}";

        if (xpBar != null)
        {
            long xpForLevel = (long)(100 * Mathf.Pow(level, 1.5f));
            xpBar.maxValue = xpForLevel;
            xpBar.value = xp;
        }
    }

    public void UpdateTapPower(int tapPower)
    {
        if (tapPowerText != null)
            tapPowerText.text = $"Тап: {tapPower}";
    }

    /// <summary>
    /// Показать floating text "+N" в мировых координатах (над персонажем).
    /// </summary>
    public void ShowFloatingText(string text, Vector3 worldPos)
    {
        if (floatingTextPrefab == null || worldCanvas == null) return;

        var go = Instantiate(floatingTextPrefab, worldCanvas.transform);
        var tmp = go.GetComponent<TextMeshProUGUI>();
        if (tmp != null)
            tmp.text = text;

        // Перевод мировых координат в экранные → Canvas
        Vector3 screenPos = mainCamera.WorldToScreenPoint(worldPos + Vector3.up * 2f);
        go.transform.position = screenPos;

        // Анимация через FloatingText компонент
        var ft = go.GetComponent<FloatingText>();
        if (ft != null) ft.Init();

        Destroy(go, 1f);
    }

    string FormatNumber(long n)
    {
        if (n >= 1_000_000_000) return $"{n / 1_000_000_000f:F1}B";
        if (n >= 1_000_000) return $"{n / 1_000_000f:F1}M";
        if (n >= 1_000) return $"{n / 1_000f:F1}K";
        return n.ToString("N0");
    }
}
