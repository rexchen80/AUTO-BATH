using UnityEngine;

public class CurvePathOnBone : MonoBehaviour
{
    [Header("曲线路径设置")]
    [SerializeField] private string pathName = "曲线路径";
    
    [Header("曲线路径点（请将骨骼下的空物体拖进来）")]
    public Transform[] controlPoints;

    // 获取路径名称（用于显示）
    public string GetPathName() => pathName;

    // 获取Catmull-Rom曲线上的点
    public Vector3 GetPointOnCurve(float t)
    {
        if (controlPoints.Length < 4) return controlPoints[0].position;
        
        // 如果想要从第一个点开始，需要特殊处理
        if (t <= 0f) return controlPoints[0].position;
        if (t >= 1f) return controlPoints[controlPoints.Length - 1].position;
        
        // 调整计算方式，让路径覆盖所有控制点
        int numSections = controlPoints.Length - 1;
        float u = t * numSections;
        int currPt = Mathf.Min(Mathf.FloorToInt(u), numSections - 1);
        u -= currPt;
        
        // 边界处理，确保索引不越界
        Vector3 p0 = controlPoints[Mathf.Max(0, currPt - 1)].position;
        Vector3 p1 = controlPoints[currPt].position;
        Vector3 p2 = controlPoints[Mathf.Min(controlPoints.Length - 1, currPt + 1)].position;
        Vector3 p3 = controlPoints[Mathf.Min(controlPoints.Length - 1, currPt + 2)].position;
        
        return 0.5f * (
            (2f * p1) +
            (-p0 + p2) * u +
            (2f * p0 - 5f * p1 + 4f * p2 - p3) * u * u +
            (-p0 + 3f * p1 - 3f * p2 + p3) * u * u * u
        );
    }

#if UNITY_EDITOR
    private void OnDrawGizmos()
    {
        if (controlPoints == null || controlPoints.Length < 4) return;
        
        // 绘制曲线
        Gizmos.color = Color.cyan;
        Vector3 prev = GetPointOnCurve(0);
        for (int i = 1; i <= 100; i++) // 增加分段数让曲线更平滑
        {
            float t = i / 100f;
            Vector3 curr = GetPointOnCurve(t);
            Gizmos.DrawLine(prev, curr);
            prev = curr;
        }
        
        // 绘制控制点
        Gizmos.color = Color.red;
        for (int i = 0; i < controlPoints.Length; i++)
        {
            if (controlPoints[i] != null)
            {
                Gizmos.DrawWireSphere(controlPoints[i].position, 0.2f);
            }
        }
        
        // 绘制控制点连线
        Gizmos.color = Color.yellow;
        for (int i = 0; i < controlPoints.Length - 1; i++)
        {
            if (controlPoints[i] != null && controlPoints[i + 1] != null)
            {
                Gizmos.DrawLine(controlPoints[i].position, controlPoints[i + 1].position);
            }
        }
    }
#endif
}