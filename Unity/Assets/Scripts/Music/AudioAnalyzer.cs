using UnityEngine;

public class AudioAnalyzer : MonoBehaviour
{
    [Header("音频设置")]
    public AudioSource audioSource;
    public int spectrumSize = 512;
    
    [Header("频率分离")]
    public float bassRange = 0.125f;      // 低音范围 (0-12.5%)
    public float midRange = 0.5f;         // 中音范围 (12.5%-50%)
    public float trebleRange = 1f;        // 高音范围 (50%-100%)
    
    // 公共数据
    public static float[] spectrumData;
    public static float bassLevel;
    public static float midLevel;
    public static float trebleLevel;
    public static float overallLevel;
    
    // 节拍检测
    public static bool beatDetected;
    private float[] beatHistory = new float[43]; // 1秒历史 (60fps * 0.7)
    private int beatIndex = 0;
    private float lastBeatTime;
    private float beatThreshold = 1.3f;
    
    void Start()
    {
        spectrumData = new float[spectrumSize];
    }
    
    void Update()
    {
        AnalyzeAudio();
        DetectBeat();
    }
    
    void AnalyzeAudio()
    {
        if (audioSource == null || !audioSource.isPlaying) return;
        
        // 获取频谱数据
        audioSource.GetSpectrumData(spectrumData, 0, FFTWindow.BlackmanHarris);
        
        // 分析不同频率范围
        int bassEnd = Mathf.FloorToInt(bassRange * spectrumSize);
        int midEnd = Mathf.FloorToInt(midRange * spectrumSize);
        
        bassLevel = GetAverageLevel(0, bassEnd);
        midLevel = GetAverageLevel(bassEnd, midEnd);
        trebleLevel = GetAverageLevel(midEnd, spectrumSize);
        overallLevel = (bassLevel + midLevel + trebleLevel) / 3f;
    }
    
    float GetAverageLevel(int start, int end)
    {
        float sum = 0f;
        for (int i = start; i < end; i++)
        {
            sum += spectrumData[i];
        }
        return sum / (end - start);
    }
    
    void DetectBeat()
    {
        // 记录低音历史
        beatHistory[beatIndex] = bassLevel;
        beatIndex = (beatIndex + 1) % beatHistory.Length;
        
        // 计算平均值
        float average = 0f;
        for (int i = 0; i < beatHistory.Length; i++)
        {
            average += beatHistory[i];
        }
        average /= beatHistory.Length;
        
        // 节拍检测
        beatDetected = bassLevel > average * beatThreshold && 
                      Time.time - lastBeatTime > 0.3f;
        
        if (beatDetected)
        {
            lastBeatTime = Time.time;
        }
    }
}