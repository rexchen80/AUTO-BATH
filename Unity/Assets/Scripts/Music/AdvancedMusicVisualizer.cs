using UnityEngine;
using System.Collections;

public class AdvancedMusicVisualizer : MonoBehaviour
{
    [Header("目标对象")]
    public Transform[] visualObjects;
    
    [Header("缩放设置")]
    public float scaleMultiplier = 5f;
    public float minScale = 0.8f;
    public float maxScale = 2f;
    public AnimationCurve scaleResponse = AnimationCurve.EaseInOut(0, 0, 1, 1);
    
    [Header("位置律动")]
    public float positionAmplitude = 2f;
    public float bassPositionMultiplier = 3f;
    public Vector3 danceDirection = Vector3.up;
    public float danceSpeed = 5f;
    
    [Header("旋转律动")]
    public bool enableRotation = true;
    public float rotationSpeed = 180f;
    public Vector3 rotationAxis = Vector3.forward;
    
    [Header("节拍响应")]
    public float beatScalePunch = 0.3f;
    public float beatRotationPunch = 45f;
    public Color beatColor = Color.white;
    public float beatColorDuration = 0.2f;
    
    [Header("高级效果")]
    public bool enablePerlinNoise = true;
    public float noiseScale = 1f;
    public float noiseSpeed = 2f;
    public bool enableWaveMotion = true;
    public float waveAmplitude = 1f;
    public float waveFrequency = 2f;
    
    private Vector3[] originalPositions;
    private Vector3[] originalScales;
    private Quaternion[] originalRotations;
    private Renderer[] renderers;
    private Color[] originalColors;
    private float time;
    private bool lastBeatState;
    
    void Start()
    {
        InitializeObjects();
    }
    
    void InitializeObjects()
    {
        int count = visualObjects.Length;
        originalPositions = new Vector3[count];
        originalScales = new Vector3[count];
        originalRotations = new Quaternion[count];
        renderers = new Renderer[count];
        originalColors = new Color[count];
        
        for (int i = 0; i < count; i++)
        {
            if (visualObjects[i] != null)
            {
                originalPositions[i] = visualObjects[i].localPosition;
                originalScales[i] = visualObjects[i].localScale;
                originalRotations[i] = visualObjects[i].localRotation;
                
                renderers[i] = visualObjects[i].GetComponent<Renderer>();
                if (renderers[i] != null)
                {
                    originalColors[i] = renderers[i].material.color;
                }
            }
        }
    }
    
    void Update()
    {
        time += Time.deltaTime;
        
        // 检测节拍触发
        if (AudioAnalyzer.beatDetected && !lastBeatState)
        {
            TriggerBeatEffect();
        }
        lastBeatState = AudioAnalyzer.beatDetected;
        
        UpdateVisualEffects();
    }
    
    void UpdateVisualEffects()
    {
        for (int i = 0; i < visualObjects.Length; i++)
        {
            if (visualObjects[i] == null) continue;
            
            // 音频响应缩放
            float scaleValue = CalculateScale(i);
            visualObjects[i].localScale = originalScales[i] * scaleValue;
            
            // 位置律动
            Vector3 newPosition = CalculatePosition(i);
            visualObjects[i].localPosition = newPosition;
            
            // 旋转律动
            if (enableRotation)
            {
                Quaternion newRotation = CalculateRotation(i);
                visualObjects[i].localRotation = newRotation;
            }
        }
    }
    
    float CalculateScale(int index)
    {
        // 基础音频响应
        float audioResponse = AudioAnalyzer.overallLevel * scaleMultiplier;
        
        // 频率分离响应
        float bassResponse = AudioAnalyzer.bassLevel * 2f;
        float midResponse = AudioAnalyzer.midLevel * 1.5f;
        float trebleResponse = AudioAnalyzer.trebleLevel * 1f;
        
        // 根据对象索引分配不同频率响应
        float frequencyResponse = 0f;
        switch (index % 3)
        {
            case 0: frequencyResponse = bassResponse; break;
            case 1: frequencyResponse = midResponse; break;
            case 2: frequencyResponse = trebleResponse; break;
        }
        
        float totalScale = 1f + audioResponse + frequencyResponse;
        totalScale = scaleResponse.Evaluate(totalScale);
        
        return Mathf.Clamp(totalScale, minScale, maxScale);
    }
    
    Vector3 CalculatePosition(int index)
    {
        Vector3 basePosition = originalPositions[index];
        
        // 音频驱动的位置变化
        float audioMovement = AudioAnalyzer.bassLevel * bassPositionMultiplier;
        Vector3 audioOffset = danceDirection * audioMovement;
        
        // Perlin噪声运动
        Vector3 noiseOffset = Vector3.zero;
        if (enablePerlinNoise)
        {
            float noiseX = Mathf.PerlinNoise(time * noiseSpeed + index, 0) - 0.5f;
            float noiseY = Mathf.PerlinNoise(0, time * noiseSpeed + index) - 0.5f;
            float noiseZ = Mathf.PerlinNoise(time * noiseSpeed + index, time * noiseSpeed + index) - 0.5f;
            
            noiseOffset = new Vector3(noiseX, noiseY, noiseZ) * noiseScale * AudioAnalyzer.midLevel;
        }
        
        // 波浪运动
        Vector3 waveOffset = Vector3.zero;
        if (enableWaveMotion)
        {
            float wave = Mathf.Sin(time * waveFrequency + index * 0.5f) * waveAmplitude;
            waveOffset = Vector3.up * wave * AudioAnalyzer.trebleLevel;
        }
        
        // 舞蹈运动
        Vector3 danceOffset = Vector3.zero;
        float dancePhase = time * danceSpeed + index * Mathf.PI * 0.5f;
        danceOffset.x = Mathf.Sin(dancePhase) * positionAmplitude * AudioAnalyzer.overallLevel;
        danceOffset.y = Mathf.Cos(dancePhase * 1.3f) * positionAmplitude * AudioAnalyzer.overallLevel;
        
        return basePosition + audioOffset + noiseOffset + waveOffset + danceOffset;
    }
    
    Quaternion CalculateRotation(int index)
    {
        // 音频驱动的旋转
        float audioRotation = AudioAnalyzer.overallLevel * rotationSpeed * Time.deltaTime;
        
        // 不同对象不同旋转方向
        float direction = (index % 2 == 0) ? 1f : -1f;
        
        // 节拍响应旋转
        float beatRotation = AudioAnalyzer.beatDetected ? beatRotationPunch : 0f;
        
        Vector3 totalRotation = rotationAxis * (audioRotation * direction + beatRotation);
        
        return originalRotations[index] * Quaternion.Euler(totalRotation);
    }
    
    void TriggerBeatEffect()
    {
        StartCoroutine(BeatPunchEffect());
        StartCoroutine(BeatColorEffect());
    }
    
    IEnumerator BeatPunchEffect()
    {
        for (int i = 0; i < visualObjects.Length; i++)
        {
            if (visualObjects[i] != null)
            {
                Vector3 punchScale = originalScales[i] * (1f + beatScalePunch);
                StartCoroutine(ScalePunch(visualObjects[i], punchScale, 0.1f));
            }
        }
        yield return null;
    }
    
    IEnumerator ScalePunch(Transform target, Vector3 targetScale, float duration)
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
    
    IEnumerator BeatColorEffect()
    {
        float elapsed = 0f;
        
        while (elapsed < beatColorDuration)
        {
            elapsed += Time.deltaTime;
            float t = 1f - (elapsed / beatColorDuration);
            
            for (int i = 0; i < renderers.Length; i++)
            {
                if (renderers[i] != null)
                {
                    Color currentColor = Color.Lerp(originalColors[i], beatColor, t);
                    renderers[i].material.color = currentColor;
                }
            }
            
            yield return null;
        }
        
        // 恢复原色
        for (int i = 0; i < renderers.Length; i++)
        {
            if (renderers[i] != null)
            {
                renderers[i].material.color = originalColors[i];
            }
        }
    }
}