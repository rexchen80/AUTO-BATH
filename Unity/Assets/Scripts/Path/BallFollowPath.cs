using UnityEngine;

public class BallFollowPath : MonoBehaviour
{
    [Header("路径组件")]
    public PathOnBone path;
    public CurvePathOnBone curvePath;
    
    [Range(0, 1)] public float t = 0f; // 路径进度，0~1

    void Update()
    {
        Vector3 pos = GetPointOnPath(t);
        transform.position = pos;
    }

    Vector3 GetPointOnPath(float t)
    {
        // 优先使用曲线路径，如果没有则使用直线路径
        if (curvePath != null)
        {
            return curvePath.GetPointOnCurve(t);
        }
        else if (path != null)
        {
            return GetPointOnLinearPath(t);
        }
        
        return transform.position;
    }

    Vector3 GetPointOnLinearPath(float t)
    {
        if (path == null || path.pathPoints == null || path.pathPoints.Length < 2) 
            return transform.position;
            
        int segCount = path.pathPoints.Length - 1;
        float totalT = t * segCount;
        int seg = Mathf.FloorToInt(totalT);
        float segT = totalT - seg;
        seg = Mathf.Clamp(seg, 0, segCount - 1);

        Vector3 p0 = path.pathPoints[seg].position;
        Vector3 p1 = path.pathPoints[seg + 1].position;
        return Vector3.Lerp(p0, p1, segT);
    }
}