using System.Collections.Generic;
using UnityEngine;

public class SimpleMocapMapper : MonoBehaviour
{
    [Header("骨骼Transform绑定")]
    public Transform head;
    public Transform leftUpperArm;
    public Transform rightUpperArm;
    public Transform leftLowerArm;
    public Transform rightLowerArm;
    public Transform leftHand;
    public Transform rightHand;
    public Transform leftUpperLeg;
    public Transform rightUpperLeg;
    public Transform leftLowerLeg;
    public Transform rightLowerLeg;
    public Transform leftFoot;
    public Transform rightFoot;

    // Mediapipe编号与骨骼Transform的映射
    private Dictionary<int, Transform> boneMap;
    // MediapipeReceiver脚本引用
    public MediapipeReceiver receiver;

    void Start()
    {
        boneMap = new Dictionary<int, Transform>
        {
            {0, head},
            {11, leftUpperArm},
            {12, rightUpperArm},
            {13, leftLowerArm},
            {14, rightLowerArm},
            {15, leftHand},
            {16, rightHand},
            {23, leftUpperLeg},
            {24, rightUpperLeg},
            {25, leftLowerLeg},
            {26, rightLowerLeg},
            {27, leftFoot},
            {28, rightFoot}
        };
    }

    void Update()
    {
        if (receiver == null || string.IsNullOrEmpty(receiver.lastJson)) return;

        try
        {
            LandmarkFrame data = JsonUtility.FromJson<LandmarkFrame>(receiver.lastJson);
            foreach (var lm in data.landmarks)
            {
                if (boneMap.ContainsKey(lm.id) && boneMap[lm.id] != null)
                {
                    boneMap[lm.id].position = new Vector3(lm.x, lm.y, lm.z);
                }
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError("解析Mediapipe JSON失败: " + ex.Message);
        }
    }
}