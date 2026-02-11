using UnityEngine;
using TMPro;

/// <summary>
/// Анимация floating text: движение вверх + fade out.
/// Вешается на префаб с TextMeshProUGUI.
/// </summary>
public class FloatingText : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 100f;
    [SerializeField] private float fadeSpeed = 2f;

    private TextMeshProUGUI tmp;
    private Color originalColor;

    public void Init()
    {
        tmp = GetComponent<TextMeshProUGUI>();
        if (tmp != null)
            originalColor = tmp.color;
    }

    void Update()
    {
        // Двигаемся вверх
        transform.position += Vector3.up * moveSpeed * Time.deltaTime;

        // Затухание
        if (tmp != null)
        {
            var c = tmp.color;
            c.a -= fadeSpeed * Time.deltaTime;
            tmp.color = c;
        }
    }
}
