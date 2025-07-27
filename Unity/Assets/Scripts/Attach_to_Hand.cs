using UnityEngine;

public class Attach_to_Hand : MonoBehaviour
{
    [Tooltip("要被附加的目标物体")]
    public Transform targetHand;
    
    [Tooltip("作为参考的VR手部物体")]
    public Transform vrHand;

    [Tooltip("是否同步位置")]
    public bool syncPosition = true;
    
    [Tooltip("是否同步旋转")]
    public bool syncRotation = true;
    
    [Tooltip("旋转偏移量 (X, Y, Z 欧拉角，单位：度)")]
    public Vector3 rotationOffset = Vector3.zero;
    
    [Tooltip("位置偏移量 (X, Y, Z 坐标)")]
    public Vector3 positionOffset = Vector3.zero;
    
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        // 检查是否已经分配了必要的引用
        if (targetHand == null)
        {
            Debug.LogError("目标物体(Target Hand)未设置!");
        }
        
        if (vrHand == null)
        {
            Debug.LogError("VR手部物体(VR Hand)未设置!");
        }
    }

    // Update is called once per frame
    void Update()
    {
        // 确保两个物体都已经分配
        if (targetHand == null || vrHand == null)
            return;
            
        // 同步位置
        if (syncPosition)
        {
            // 应用位置偏移量
            targetHand.position = vrHand.position + vrHand.TransformDirection(positionOffset);
        }
        
        // 同步旋转
        if (syncRotation)
        {
            // 应用旋转偏移量
            Quaternion offsetRotation = Quaternion.Euler(rotationOffset);
            targetHand.rotation = vrHand.rotation * offsetRotation;
        }
    }
}
