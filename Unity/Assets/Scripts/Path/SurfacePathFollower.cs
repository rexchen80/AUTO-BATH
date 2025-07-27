using UnityEngine;

public class SurfacePathFollower : MonoBehaviour
{
    [Header("路径控制点")]
    public Transform[] pathPoints;
    
    [Header("运动设置")]
    [Range(0, 1)] public float progress = 0f;
    public bool autoMove = false;
    public float moveSpeed = 0.5f;
    
    [Header("物理约束")]
    public float sphereRadius = 0.02f; // 小球半径
    public LayerMask surfaceLayer = -1;
    public float pushForce = 100f; // 推出表面的力度

    void Start()
    {
        // 确保小球有刚体和碰撞体
        if (GetComponent<Rigidbody>() == null)
        {
            Rigidbody rb = gameObject.AddComponent<Rigidbody>();
            rb.useGravity = false;
            rb.freezeRotation = true;
        }
        
        if (GetComponent<SphereCollider>() == null)
        {
            SphereCollider col = gameObject.AddComponent<SphereCollider>();
            col.radius = sphereRadius;
        }
    }

    void Update()
    {
        if (autoMove)
        {
            progress += Time.deltaTime * moveSpeed;
            if (progress > 1f) progress = 0f;
        }
        
        UpdateBallPosition();
    }

    void UpdateBallPosition()
    {
        if (pathPoints == null || pathPoints.Length < 2) return;

        Vector3 targetPoint = GetPathPoint(progress);
        // 直接设置位置
        transform.position = targetPoint;
        // 设置角度：朝向切线方向
        Vector3 tangent = GetPathTangent(progress);
        transform.rotation = Quaternion.LookRotation(tangent, Vector3.up);
        // 如果有Rigidbody，归零速度
        Rigidbody rb = GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.linearVelocity = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
        }
    }

    Vector3 GetPathPoint(float t)
    {
        t = Mathf.Clamp01(t);
        if (pathPoints.Length < 2) return transform.position;
        if (pathPoints.Length == 2)
        {
            return Vector3.Lerp(pathPoints[0].position, pathPoints[1].position, t);
        }
        float segmentCount = pathPoints.Length - 1;
        float segmentPos = t * segmentCount;
        int segmentIndex = Mathf.FloorToInt(segmentPos);
        if (segmentIndex >= pathPoints.Length - 1)
        {
            return pathPoints[pathPoints.Length - 1].position;
        }
        float localT = segmentPos - segmentIndex;
        return Vector3.Lerp(pathPoints[segmentIndex].position, pathPoints[segmentIndex + 1].position, localT);
    }

    // 新增：获取路径切线
    Vector3 GetPathTangent(float t)
    {
        float delta = 0.001f;
        float t2 = Mathf.Clamp01(t + delta);
        Vector3 p1 = GetPathPoint(t);
        Vector3 p2 = GetPathPoint(t2);
        return (p2 - p1).normalized;
    }

    void OnCollisionStay(Collision collision)
    {
        // 当与表面碰撞时，施加一个向外的力防止穿模
        if (((1 << collision.gameObject.layer) & surfaceLayer) != 0)
        {
            Rigidbody rb = GetComponent<Rigidbody>();
            if (rb != null)
            {
                foreach (ContactPoint contact in collision.contacts)
                {
                    Vector3 pushDirection = contact.normal;
                    rb.AddForce(pushDirection * pushForce * Time.deltaTime, ForceMode.Force);
                }
            }
        }
    }
}