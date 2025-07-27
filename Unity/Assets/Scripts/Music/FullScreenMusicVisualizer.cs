using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;

public class FullScreenMusicVisualizer : MonoBehaviour
{
    [Header("Canvas设置")]
    public Canvas mainCanvas;
    public CanvasScaler canvasScaler;
    
    [Header("文字元素")]
    public TextMeshProUGUI[] rhythmTexts;
    public Text[] legacyTexts;
    
    [Header("图像元素")]
    public Image[] rhythmImages;
    public RawImage[] rhythmRawImages;
    public RectTransform[] customUIElements;
    
    [Header("文字律动设置")]
    public float textScaleMultiplier = 2f;
    public float textMinScale = 0.8f;
    public float textMaxScale = 1.5f;
    public Vector2 textPositionRange = new Vector2(50f, 100f);
    public float textRotationRange = 15f;
    
    [Header("图像律动设置")]
    public float imageScaleMultiplier = 3f;
    public float imageMinScale = 0.9f;
    public float imageMaxScale = 2f;
    public Vector2 imagePositionRange = new Vector2(30f, 80f);
    public float imageRotationRange = 20f;
    
    [Header("颜色律动")]
    public bool enableColorChange = true;
    public Color bassColor = Color.red;
    public Color midColor = Color.green;
    public Color trebleColor = Color.blue;
    public float colorIntensity = 0.8f;
    
    [Header("特效设置")]
    public bool enableGlow = true;
    public bool enablePulse = true;
    public bool enableFloat = true;
    public float glowIntensity = 2f;
    public float pulseSpeed = 5f;
    public float floatAmplitude = 100f;
    
    [Header("节拍特效")]
    public float beatPunchScale = 0.3f;
    public float beatShakeIntensity = 20f;
    public float beatFlashDuration = 0.15f;
    public Color beatFlashColor = Color.white;
    
    private struct UIElementData
    {
        public RectTransform rectTransform;
        public Vector2 originalPosition;
        public Vector3 originalScale;
        public float originalRotation;
        public Graphic graphic;
        public Color originalColor;
        public int frequencyGroup; // 0=bass, 1=mid, 2=treble
    }
    
    private List<UIElementData> allElements = new List<UIElementData>();
    private bool lastBeatState;
    private float time;
    
    void Start()
    {
        SetupFullScreen();
        InitializeElements();
    }
    
    void SetupFullScreen()
    {
        // 确保Canvas是全屏的
        if (mainCanvas == null)
            mainCanvas = FindObjectOfType<Canvas>();
            
        if (mainCanvas != null)
        {
            mainCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
            mainCanvas.sortingOrder = 1000;
        }
        
        // 设置Canvas Scaler为适应屏幕
        if (canvasScaler == null)
            canvasScaler = mainCanvas.GetComponent<CanvasScaler>();
            
        if (canvasScaler != null)
        {
            canvasScaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            canvasScaler.referenceResolution = new Vector2(1920, 1080);
            canvasScaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            canvasScaler.matchWidthOrHeight = 0.5f;
        }
    }
    
    void InitializeElements()
    {
        allElements.Clear();
        
        // 添加TextMeshPro文字
        for (int i = 0; i < rhythmTexts.Length; i++)
        {
            if (rhythmTexts[i] != null)
            {
                AddUIElement(rhythmTexts[i].rectTransform, rhythmTexts[i], i);
            }
        }
        
        // 添加Legacy Text
        for (int i = 0; i < legacyTexts.Length; i++)
        {
            if (legacyTexts[i] != null)
            {
                AddUIElement(legacyTexts[i].rectTransform, legacyTexts[i], i);
            }
        }
        
        // 添加Image
        for (int i = 0; i < rhythmImages.Length; i++)
        {
            if (rhythmImages[i] != null)
            {
                AddUIElement(rhythmImages[i].rectTransform, rhythmImages[i], i);
            }
        }
        
        // 添加RawImage
        for (int i = 0; i < rhythmRawImages.Length; i++)
        {
            if (rhythmRawImages[i] != null)
            {
                AddUIElement(rhythmRawImages[i].rectTransform, rhythmRawImages[i], i);
            }
        }
        
        // 添加自定义UI元素
        for (int i = 0; i < customUIElements.Length; i++)
        {
            if (customUIElements[i] != null)
            {
                Graphic graphic = customUIElements[i].GetComponent<Graphic>();
                AddUIElement(customUIElements[i], graphic, i);
            }
        }
    }
    
    void AddUIElement(RectTransform rectTransform, Graphic graphic, int index)
    {
        UIElementData data = new UIElementData
        {
            rectTransform = rectTransform,
            originalPosition = rectTransform.anchoredPosition,
            originalScale = rectTransform.localScale,
            originalRotation = rectTransform.localEulerAngles.z,
            graphic = graphic,
            originalColor = graphic != null ? graphic.color : Color.white,
            frequencyGroup = index % 3 // 分配到不同频率组
        };
        
        allElements.Add(data);
    }
    
    void Update()
    {
        time += Time.deltaTime;
        
        // 检测节拍
        if (AudioAnalyzer.beatDetected && !lastBeatState)
        {
            TriggerBeatEffects();
        }
        lastBeatState = AudioAnalyzer.beatDetected;
        
        UpdateAllElements();
    }
    
    void UpdateAllElements()
    {
        for (int i = 0; i < allElements.Count; i++)
        {
            UpdateUIElement(i);
        }
    }
    
    void UpdateUIElement(int index)
    {
        UIElementData data = allElements[index];
        if (data.rectTransform == null) return;
        
        // 获取对应频率的音频数据
        float audioLevel = GetAudioLevelForFrequency(data.frequencyGroup);
        
        // 更新缩放
        UpdateScale(data, audioLevel, index);
        
        // 更新位置
        UpdatePosition(data, audioLevel, index);
        
        // 更新旋转
        UpdateRotation(data, audioLevel, index);
        
        // 更新颜色
        if (enableColorChange)
        {
            UpdateColor(data, index);
        }
    }
    
    float GetAudioLevelForFrequency(int frequencyGroup)
    {
        switch (frequencyGroup)
        {
            case 0: return AudioAnalyzer.bassLevel;
            case 1: return AudioAnalyzer.midLevel;
            case 2: return AudioAnalyzer.trebleLevel;
            default: return AudioAnalyzer.overallLevel;
        }
    }
    
    void UpdateScale(UIElementData data, float audioLevel, int index)
    {
        // 基础音频响应
        bool isText = data.graphic is Text || data.graphic is TextMeshProUGUI;
        float multiplier = isText ? textScaleMultiplier : imageScaleMultiplier;
        float minScale = isText ? textMinScale : imageMinScale;
        float maxScale = isText ? textMaxScale : imageMaxScale;
        
        float scaleValue = 1f + audioLevel * multiplier;
        
        // 添加脉冲效果
        if (enablePulse)
        {
            float pulse = Mathf.Sin(time * pulseSpeed + index) * 0.1f * audioLevel;
            scaleValue += pulse;
        }
        
        scaleValue = Mathf.Clamp(scaleValue, minScale, maxScale);
        data.rectTransform.localScale = data.originalScale * scaleValue;
    }
    
    void UpdatePosition(UIElementData data, float audioLevel, int index)
    {
        Vector2 newPosition = data.originalPosition;
        
        // 音频驱动的位置变化
        bool isText = data.graphic is Text || data.graphic is TextMeshProUGUI;
        Vector2 positionRange = isText ? textPositionRange : imagePositionRange;
        
        // 基于频率的运动模式
        switch (data.frequencyGroup)
        {
            case 0: // Bass - 垂直运动
                newPosition.y += Mathf.Sin(time * 3f + index) * positionRange.y * audioLevel;
                break;
            case 1: // Mid - 水平运动
                newPosition.x += Mathf.Cos(time * 4f + index) * positionRange.x * audioLevel;
                break;
            case 2: // Treble - 圆周运动
                float angle = time * 5f + index;
                newPosition.x += Mathf.Cos(angle) * positionRange.x * audioLevel;
                newPosition.y += Mathf.Sin(angle) * positionRange.y * audioLevel;
                break;
        }
        
        // 浮动效果
        if (enableFloat)
        {
            float floatOffset = Mathf.PerlinNoise(time + index, time + index) - 0.5f;
            newPosition += Vector2.one * floatOffset * floatAmplitude * audioLevel;
        }
        
        data.rectTransform.anchoredPosition = newPosition;
    }
    
    void UpdateRotation(UIElementData data, float audioLevel, int index)
    {
        bool isText = data.graphic is Text || data.graphic is TextMeshProUGUI;
        float rotationRange = isText ? textRotationRange : imageRotationRange;
        
        float rotation = data.originalRotation;
        
        // 音频驱动的旋转
        rotation += Mathf.Sin(time * 2f + index) * rotationRange * audioLevel;
        
        // 不同频率组的旋转方向
        float direction = (data.frequencyGroup % 2 == 0) ? 1f : -1f;
        rotation *= direction;
        
        data.rectTransform.localEulerAngles = new Vector3(0, 0, rotation);
    }
    
    void UpdateColor(UIElementData data, int index)
    {
        if (data.graphic == null) return;
        
        // 根据频率组选择颜色
        Color targetColor = data.originalColor;
        
        switch (data.frequencyGroup)
        {
            case 0:
                targetColor = Color.Lerp(data.originalColor, bassColor, 
                    AudioAnalyzer.bassLevel * colorIntensity);
                break;
            case 1:
                targetColor = Color.Lerp(data.originalColor, midColor, 
                    AudioAnalyzer.midLevel * colorIntensity);
                break;
            case 2:
                targetColor = Color.Lerp(data.originalColor, trebleColor, 
                    AudioAnalyzer.trebleLevel * colorIntensity);
                break;
        }
        
        // 添加发光效果
        if (enableGlow)
        {
            float glow = AudioAnalyzer.overallLevel * glowIntensity;
            targetColor.r = Mathf.Clamp01(targetColor.r + glow);
            targetColor.g = Mathf.Clamp01(targetColor.g + glow);
            targetColor.b = Mathf.Clamp01(targetColor.b + glow);
        }
        
        data.graphic.color = targetColor;
    }
    
    void TriggerBeatEffects()
    {
        StartCoroutine(BeatPunchEffect());
        StartCoroutine(BeatShakeEffect());
        
        if (enableColorChange)
        {
            StartCoroutine(BeatFlashEffect());
        }
    }
    
    IEnumerator BeatPunchEffect()
    {
        for (int i = 0; i < allElements.Count; i++)
        {
            if (allElements[i].rectTransform != null)
            {
                Vector3 punchScale = allElements[i].originalScale * (1f + beatPunchScale);
                StartCoroutine(ScalePunch(allElements[i].rectTransform, punchScale, 0.1f));
            }
        }
        yield return null;
    }
    
    IEnumerator BeatShakeEffect()
    {
        float duration = 0.1f;
        float elapsed = 0f;
        
        while (elapsed < duration)
        {
            for (int i = 0; i < allElements.Count; i++)
            {
                if (allElements[i].rectTransform != null)
                {
                    Vector2 shake = Random.insideUnitCircle * beatShakeIntensity;
                    allElements[i].rectTransform.anchoredPosition = 
                        allElements[i].originalPosition + shake;
                }
            }
            
            elapsed += Time.deltaTime;
            yield return null;
        }
        
        // 恢复原位置
        for (int i = 0; i < allElements.Count; i++)
        {
            if (allElements[i].rectTransform != null)
            {
                allElements[i].rectTransform.anchoredPosition = allElements[i].originalPosition;
            }
        }
    }
    
    IEnumerator BeatFlashEffect()
    {
        float elapsed = 0f;
        
        while (elapsed < beatFlashDuration)
        {
            float t = 1f - (elapsed / beatFlashDuration);
            
            for (int i = 0; i < allElements.Count; i++)
            {
                if (allElements[i].graphic != null)
                {
                    Color flashColor = Color.Lerp(allElements[i].originalColor, beatFlashColor, t);
                    allElements[i].graphic.color = flashColor;
                }
            }
            
            elapsed += Time.deltaTime;
            yield return null;
        }
    }
    
    IEnumerator ScalePunch(RectTransform target, Vector3 targetScale, float duration)
    {
        Vector3 startScale = target.localScale;
        float elapsed = 0f;
        
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / duration;
            t = 1f - (1f - t) * (1f - t); // EaseOut
            
            target.localScale = Vector3.Lerp(startScale, targetScale, t);
            yield return null;
        }
    }
}