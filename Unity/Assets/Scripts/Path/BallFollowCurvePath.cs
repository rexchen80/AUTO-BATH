using UnityEngine;

public class BallFollowCurvePath : MonoBehaviour
{
    public CurvePathOnBone curvePath;
    [Range(0, 1)] public float t = 0f; // 路径进度，0~1
    
    [Header("自动寻路设置")]
    public bool autoFollow = true;        // 是否自动跟随路径
    public float speed = 0.5f;           // 移动速度
    public bool loop = true;             // 是否循环
    public bool pingPong = false;        // 是否来回运动
    
    [Header("运动选项")]
    public AnimationCurve speedCurve = AnimationCurve.Linear(0, 1, 1, 1); // 速度曲线
    public bool faceDirection = true;     // 是否面向运动方向
    public float rotationSpeed = 10f;     // 旋转速度
    
    [Header("调试信息")]
    [Space]
    public bool showDebugInfo = false;    // 显示调试信息
    
    private bool isReversing = false;     // 是否正在反向运动（用于pingPong模式）
    private float currentSpeed;           // 当前速度
    
    void Update()
    {
        if (curvePath == null || curvePath.controlPoints == null || curvePath.controlPoints.Length < 4) 
            return;
            
        // 自动移动
        if (autoFollow)
        {
            UpdateAutoMovement();
        }
        
        // 更新位置
        Vector3 pos = curvePath.GetPointOnCurve(t);
        transform.position = pos;
        
        // 面向运动方向
        if (autoFollow && faceDirection)
        {
            UpdateRotation();
        }
    }
    
    void UpdateAutoMovement()
    {
        // 根据速度曲线计算当前速度
        currentSpeed = speed * speedCurve.Evaluate(t) * Time.deltaTime;
        
        if (pingPong)
        {
            // 来回运动模式
            if (!isReversing)
            {
                t += currentSpeed;
                if (t >= 1f)
                {
                    t = 1f;
                    isReversing = true;
                }
            }
            else
            {
                t -= currentSpeed;
                if (t <= 0f)
                {
                    t = 0f;
                    isReversing = false;
                }
            }
        }
        else
        {
            // 正常前进或循环模式
            t += currentSpeed;
            
            if (t >= 1f)
            {
                if (loop)
                {
                    t = 0f; // 重新开始
                }
                else
                {
                    t = 1f;
                    autoFollow = false; // 停止自动跟随
                }
            }
        }
    }
    
    void UpdateRotation()
    {
        // 计算前方一小段距离的点来确定方向
        float lookAheadDistance = 0.01f;
        float lookAheadT = t + lookAheadDistance;
        
        // 处理边界情况
        if (pingPong && isReversing)
        {
            lookAheadT = t - lookAheadDistance;
        }
        
        // 确保t值在有效范围内
        lookAheadT = Mathf.Clamp01(lookAheadT);
        
        Vector3 currentPos = curvePath.GetPointOnCurve(t);
        Vector3 futurePos = curvePath.GetPointOnCurve(lookAheadT);
        
        Vector3 direction = (futurePos - currentPos).normalized;
        
        if (direction != Vector3.zero)
        {
            Quaternion targetRotation = Quaternion.LookRotation(direction);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, 
                rotationSpeed * Time.deltaTime);
        }
    }
    
    // 在Inspector中显示的控制按钮
    [ContextMenu("开始自动跟随")]
    public void StartAutoFollow()
    {
        autoFollow = true;
    }
    
    [ContextMenu("停止自动跟随")]
    public void StopAutoFollow()
    {
        autoFollow = false;
    }
    
    [ContextMenu("重置到起点")]
    public void ResetToStart()
    {
        t = 0f;
        isReversing = false;
    }
    
    [ContextMenu("跳到终点")]
    public void JumpToEnd()
    {
        t = 1f;
        isReversing = false;
    }
    
    // 公共方法供其他脚本调用
    public void SetSpeed(float newSpeed)
    {
        speed = newSpeed;
    }
    
    public void SetProgress(float progress)
    {
        t = Mathf.Clamp01(progress);
    }
    
    public float GetProgress()
    {
        return t;
    }
    
    public bool IsAtEnd()
    {
        return t >= 1f && !loop && !pingPong;
    }
    
    public bool IsAtStart()
    {
        return t <= 0f;
    }
}