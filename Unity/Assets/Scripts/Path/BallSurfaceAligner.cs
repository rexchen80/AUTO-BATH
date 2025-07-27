using UnityEngine;

public class BallSurfaceAligner : MonoBehaviour
{
    [Header("目标表面")]
    public Transform targetMeshTransform; // 拖入HumanM_BodyMesh
    
    [Header("对齐设置")]
    [Range(0.1f, 10f)]
    public float detectionRadius = 1f; // 检测半径
    
    [Range(1f, 20f)]
    public float smoothSpeed = 10f; // 旋转平滑速度
    
    [Header("调试")]
    public bool showDebugRays = true;
    
    private Mesh targetMesh;
    private Vector3[] vertices;
    private int[] triangles;
    private Vector3 lastValidNormal = Vector3.up;

    void Start()
    {
        // 获取目标网格
        if (targetMeshTransform != null)
        {
            MeshFilter meshFilter = targetMeshTransform.GetComponent<MeshFilter>();
            if (meshFilter != null)
            {
                targetMesh = meshFilter.mesh;
                vertices = targetMesh.vertices;
                triangles = targetMesh.triangles;
            }
            else
            {
                SkinnedMeshRenderer skinnedMeshRenderer = targetMeshTransform.GetComponent<SkinnedMeshRenderer>();
                if (skinnedMeshRenderer != null)
                {
                    targetMesh = new Mesh();
                    skinnedMeshRenderer.BakeMesh(targetMesh);
                    vertices = targetMesh.vertices;
                    triangles = targetMesh.triangles;
                }
            }
        }
    }

    void Update()
    {
        if (targetMesh == null || targetMeshTransform == null) return;

        // 获取最近的表面法向量
        Vector3 surfaceNormal = GetClosestSurfaceNormal();
        
        if (surfaceNormal != Vector3.zero)
        {
            lastValidNormal = surfaceNormal;
        }
        else
        {
            surfaceNormal = lastValidNormal;
        }

        // 计算目标旋转（Z轴对齐到表面法向量）
        Quaternion targetRotation = Quaternion.FromToRotation(Vector3.forward, surfaceNormal);
        
        // 平滑旋转
        transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * smoothSpeed);
    }

    Vector3 GetClosestSurfaceNormal()
    {
        if (targetMesh == null) return Vector3.zero;

        // 更新蒙皮网格（如果是SkinnedMeshRenderer）
        SkinnedMeshRenderer skinnedRenderer = targetMeshTransform.GetComponent<SkinnedMeshRenderer>();
        if (skinnedRenderer != null)
        {
            skinnedRenderer.BakeMesh(targetMesh);
            vertices = targetMesh.vertices;
        }

        Vector3 ballPosition = transform.position;
        Vector3 closestPoint = Vector3.zero;
        Vector3 closestNormal = Vector3.zero;
        float closestDistance = float.MaxValue;

        // 将小球位置转换到网格的本地空间
        Vector3 localBallPos = targetMeshTransform.InverseTransformPoint(ballPosition);

        // 遍历所有三角形找到最近的点
        for (int i = 0; i < triangles.Length; i += 3)
        {
            Vector3 v0 = vertices[triangles[i]];
            Vector3 v1 = vertices[triangles[i + 1]];
            Vector3 v2 = vertices[triangles[i + 2]];

            // 计算三角形上最近的点
            Vector3 pointOnTriangle = ClosestPointOnTriangle(localBallPos, v0, v1, v2);
            float distance = Vector3.Distance(localBallPos, pointOnTriangle);

            if (distance < closestDistance && distance <= detectionRadius)
            {
                closestDistance = distance;
                closestPoint = pointOnTriangle;
                
                // 计算三角形法向量
                Vector3 edge1 = v1 - v0;
                Vector3 edge2 = v2 - v0;
                Vector3 normal = Vector3.Cross(edge1, edge2).normalized;
                
                // 转换到世界空间
                closestNormal = targetMeshTransform.TransformDirection(normal);
            }
        }

        return closestNormal;
    }

    Vector3 ClosestPointOnTriangle(Vector3 point, Vector3 a, Vector3 b, Vector3 c)
    {
        Vector3 ab = b - a;
        Vector3 ac = c - a;
        Vector3 ap = point - a;

        float d1 = Vector3.Dot(ab, ap);
        float d2 = Vector3.Dot(ac, ap);
        if (d1 <= 0f && d2 <= 0f) return a;

        Vector3 bp = point - b;
        float d3 = Vector3.Dot(ab, bp);
        float d4 = Vector3.Dot(ac, bp);
        if (d3 >= 0f && d4 <= d3) return b;

        Vector3 cp = point - c;
        float d5 = Vector3.Dot(ab, cp);
        float d6 = Vector3.Dot(ac, cp);
        if (d6 >= 0f && d5 <= d6) return c;

        float vc = d1 * d4 - d3 * d2;
        if (vc <= 0f && d1 >= 0f && d3 <= 0f)
        {
            float v = d1 / (d1 - d3);
            return a + v * ab;
        }

        float vb = d5 * d2 - d1 * d6;
        if (vb <= 0f && d2 >= 0f && d6 <= 0f)
        {
            float w = d2 / (d2 - d6);
            return a + w * ac;
        }

        float va = d3 * d6 - d5 * d4;
        if (va <= 0f && (d4 - d3) >= 0f && (d5 - d6) >= 0f)
        {
            float w = (d4 - d3) / ((d4 - d3) + (d5 - d6));
            return b + w * (c - b);
        }

        float denom = 1f / (va + vb + vc);
        float v2 = vb * denom;
        float w2 = vc * denom;
        return a + ab * v2 + ac * w2;
    }

    void OnDrawGizmos()
    {
        if (!showDebugRays) return;

        // 绘制检测半径
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, detectionRadius);

        // 绘制Z轴方向（应该垂直于表面）
        Gizmos.color = Color.blue;
        Gizmos.DrawRay(transform.position, transform.forward * 2f);

        // 绘制当前法向量
        Gizmos.color = Color.green;
        Gizmos.DrawRay(transform.position, lastValidNormal * 1.5f);
    }
}