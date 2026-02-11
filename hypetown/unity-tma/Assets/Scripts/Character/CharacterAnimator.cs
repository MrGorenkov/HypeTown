using UnityEngine;

/// <summary>
/// Контроллер анимаций персонажа.
/// Idle → TapReaction → Idle. Анимации из Mixamo.
/// Поддерживает как Animator (для Mixamo-моделей), так и простой скрипт-fallback.
/// </summary>
public class CharacterAnimator : MonoBehaviour
{
    private Animator animator;
    private bool hasAnimator;

    // Fallback-анимация (если нет Animator)
    private Vector3 originalScale;
    private float bounceTimer;
    private bool isBouncing;

    // Хеши анимационных состояний (Mixamo)
    private static readonly int TapTrigger = Animator.StringToHash("Tap");
    private static readonly int IdleBool = Animator.StringToHash("IsIdle");
    private static readonly int VictoryTrigger = Animator.StringToHash("Victory");
    private static readonly int DefeatTrigger = Animator.StringToHash("Defeat");

    void Awake()
    {
        animator = GetComponent<Animator>();
        hasAnimator = animator != null && animator.runtimeAnimatorController != null;
        originalScale = transform.localScale;
    }

    /// <summary>
    /// Реакция на тап — подпрыгивание / анимация Mixamo "Clap" или "Excited".
    /// </summary>
    public void PlayTapReaction()
    {
        if (hasAnimator)
        {
            animator.SetTrigger(TapTrigger);
        }
        else
        {
            // Fallback: скейл-bounce
            isBouncing = true;
            bounceTimer = 0f;
        }
    }

    /// <summary>
    /// Победная анимация (PvP victory).
    /// </summary>
    public void PlayVictory()
    {
        if (hasAnimator)
            animator.SetTrigger(VictoryTrigger);
    }

    /// <summary>
    /// Анимация поражения (PvP defeat).
    /// </summary>
    public void PlayDefeat()
    {
        if (hasAnimator)
            animator.SetTrigger(DefeatTrigger);
    }

    void Update()
    {
        if (!isBouncing) return;

        bounceTimer += Time.deltaTime * 8f;
        float bounce = Mathf.Sin(bounceTimer * Mathf.PI) * 0.15f;
        transform.localScale = originalScale * (1f + bounce);

        if (bounceTimer >= 1f)
        {
            isBouncing = false;
            transform.localScale = originalScale;
        }
    }
}
