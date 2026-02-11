using UnityEngine;
using System.Collections;

/// <summary>
/// Менеджер кликера: обработка тапов, батчинг, анимации.
/// Тапы по 3D-персонажу → начисление монет → синхронизация с сервером.
/// </summary>
public class TapManager : MonoBehaviour
{
    [Header("Настройки")]
    [SerializeField] private float syncInterval = 2f;   // Батч-синхронизация каждые 2 сек
    [SerializeField] private int maxBatchSize = 50;       // Макс тапов за батч
    [SerializeField] private LayerMask characterLayer;    // Слой персонажа для Raycast

    [Header("Ссылки")]
    [SerializeField] private Camera mainCamera;
    [SerializeField] private ParticleSystem tapVFX;       // Эффект при тапе

    private int pendingTaps = 0;
    private Coroutine syncCoroutine;

    void Start()
    {
        if (mainCamera == null)
            mainCamera = Camera.main;

        syncCoroutine = StartCoroutine(SyncLoop());
    }

    void Update()
    {
        HandleInput();
    }

    void HandleInput()
    {
        // Мобильный тач или клик мыши
        bool tapped = false;
        Vector3 inputPos = Vector3.zero;

        if (Input.touchCount > 0)
        {
            Touch touch = Input.GetTouch(0);
            if (touch.phase == TouchPhase.Began)
            {
                tapped = true;
                inputPos = touch.position;
            }
        }
        else if (Input.GetMouseButtonDown(0))
        {
            tapped = true;
            inputPos = Input.mousePosition;
        }

        if (!tapped) return;

        // Raycast на персонажа
        Ray ray = mainCamera.ScreenPointToRay(inputPos);
        if (Physics.Raycast(ray, out RaycastHit hit, 100f, characterLayer))
        {
            ProcessTap(hit.point);
        }
    }

    void ProcessTap(Vector3 hitPoint)
    {
        var gm = GameManager.Instance;
        int tapPower = gm.Player.TapPower;

        // Начислить локально
        gm.AddCoins(tapPower);
        pendingTaps++;

        // VFX
        if (tapVFX != null)
        {
            tapVFX.transform.position = hitPoint;
            tapVFX.Play();
        }

        // Анимация персонажа
        var character = gm.CharacterLoader.CurrentCharacter;
        if (character != null)
        {
            var anim = character.GetComponent<CharacterAnimator>();
            if (anim != null)
                anim.PlayTapReaction();
        }

        // Floating text (+N)
        gm.UIManager.ShowFloatingText($"+{tapPower}", hitPoint);
    }

    IEnumerator SyncLoop()
    {
        while (true)
        {
            yield return new WaitForSeconds(syncInterval);

            if (pendingTaps > 0)
            {
                int tapsToSend = Mathf.Min(pendingTaps, maxBatchSize);
                pendingTaps -= tapsToSend;
                _ = GameManager.Instance.ApiClient.SendTaps(tapsToSend);
            }
        }
    }

    void OnDestroy()
    {
        // Финальная синхронизация
        if (pendingTaps > 0)
        {
            _ = GameManager.Instance.ApiClient.SendTaps(pendingTaps);
        }
    }
}
