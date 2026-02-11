using UnityEngine;
using System.Threading.Tasks;
using UnityEngine.Networking;

/// <summary>
/// Загрузчик 3D-моделей персонажей.
/// Загружает GLB из URL (S3/Cloudinary), парсит через GLTFUtility.
/// Если модель не задана — использует дефолтную по архетипу.
/// </summary>
public class CharacterLoader : MonoBehaviour
{
    [Header("Настройки")]
    [SerializeField] private Transform spawnPoint;
    [SerializeField] private float modelScale = 1f;

    [Header("Дефолтные модели по архетипу")]
    [SerializeField] private GameObject directorPrefab;
    [SerializeField] private GameObject streamerPrefab;
    [SerializeField] private GameObject producerPrefab;
    [SerializeField] private GameObject magnatePrefab;
    [SerializeField] private GameObject bloggerPrefab;
    [SerializeField] private GameObject journalistPrefab;

    public GameObject CurrentCharacter { get; private set; }

    /// <summary>
    /// Загрузить GLB-модель по URL (TripoSR / Cloudinary).
    /// Требует GLTFUtility плагин (https://github.com/Siccity/GLTFUtility).
    /// </summary>
    public async Task LoadCharacterModel(string glbUrl)
    {
        Debug.Log($"[CharacterLoader] Загрузка GLB: {glbUrl}");

        using var request = UnityWebRequest.Get(glbUrl);
        var operation = request.SendWebRequest();

        while (!operation.isDone)
            await Task.Yield();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[CharacterLoader] Ошибка загрузки GLB: {request.error}");
            return;
        }

        byte[] glbData = request.downloadHandler.data;

        // GLTFUtility: Importer.LoadFromBytes(glbData)
        // Если GLTFUtility не подключён — используем заглушку
        #if GLTF_UTILITY
        GameObject model = Siccity.GLTFUtility.Importer.LoadFromBytes(glbData);
        #else
        Debug.LogWarning("[CharacterLoader] GLTFUtility не установлен, загружаю дефолтную модель");
        GameObject model = null;
        #endif

        if (model != null)
        {
            SpawnCharacter(model);
        }
        else
        {
            LoadDefaultModel(GameManager.Instance.Player.Archetype);
        }
    }

    /// <summary>
    /// Загрузить дефолтный префаб по архетипу.
    /// </summary>
    public void LoadDefaultModel(string archetype)
    {
        GameObject prefab = archetype switch
        {
            "director"   => directorPrefab,
            "streamer"   => streamerPrefab,
            "producer"   => producerPrefab,
            "magnate"    => magnatePrefab,
            "blogger"    => bloggerPrefab,
            "journalist" => journalistPrefab,
            _            => directorPrefab,
        };

        if (prefab == null)
        {
            Debug.LogWarning($"[CharacterLoader] Нет префаба для архетипа: {archetype}");
            return;
        }

        GameObject model = Instantiate(prefab);
        SpawnCharacter(model);
    }

    void SpawnCharacter(GameObject model)
    {
        // Удалить предыдущего
        if (CurrentCharacter != null)
            Destroy(CurrentCharacter);

        model.transform.SetParent(spawnPoint, false);
        model.transform.localPosition = Vector3.zero;
        model.transform.localScale = Vector3.one * modelScale;
        model.layer = LayerMask.NameToLayer("Character");

        // Добавить коллайдер для raycast (тап)
        if (model.GetComponent<Collider>() == null)
        {
            var box = model.AddComponent<BoxCollider>();
            // Авто-подгонка размера
            var renderers = model.GetComponentsInChildren<Renderer>();
            if (renderers.Length > 0)
            {
                Bounds bounds = renderers[0].bounds;
                foreach (var r in renderers)
                    bounds.Encapsulate(r.bounds);
                box.center = model.transform.InverseTransformPoint(bounds.center);
                box.size = bounds.size / modelScale;
            }
        }

        // Добавить аниматор
        if (model.GetComponent<CharacterAnimator>() == null)
            model.AddComponent<CharacterAnimator>();

        CurrentCharacter = model;
        Debug.Log("[CharacterLoader] Персонаж загружен");
    }
}
