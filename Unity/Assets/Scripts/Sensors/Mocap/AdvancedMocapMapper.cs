using System.Collections.Generic;
using UnityEngine;

public class AdvancedMocapMapper : MonoBehaviour
{
    [Header("骨骼Transform绑定")]
    public Transform hips;
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

    [Header("坐标变换参数")]
    public float scale = 1.0f;
    public Vector3 offset = Vector3.zero;

    public MediapipeReceiver receiver;
    private Dictionary<int, Vector3> mpPoints = new Dictionary<int, Vector3>();

    void Update()
    {
        if (receiver == null || string.IsNullOrEmpty(receiver.lastJson)) return;

        try
        {
            LandmarkFrame data = JsonUtility.FromJson<LandmarkFrame>(receiver.lastJson);
            mpPoints.Clear();
            foreach (var lm in data.landmarks)
            {
                Vector3 pos = new Vector3(lm.x, lm.y, lm.z) * scale + offset;
                mpPoints[lm.id] = pos;
            }

            // 1. 驱动hips位置
            if (mpPoints.ContainsKey(23) && mpPoints.ContainsKey(24) && hips != null)
            {
                hips.position = (mpPoints[23] + mpPoints[24]) / 2f;
            }

            // 2. 上臂和下臂旋转
            if (mpPoints.ContainsKey(11) && mpPoints.ContainsKey(13) && leftUpperArm != null)
            {
                Vector3 dir = (mpPoints[13] - mpPoints[11]).normalized;
                leftUpperArm.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(13) && mpPoints.ContainsKey(15) && leftLowerArm != null)
            {
                Vector3 dir = (mpPoints[15] - mpPoints[13]).normalized;
                leftLowerArm.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            // 用旋转驱动手掌
            if (mpPoints.ContainsKey(13) && mpPoints.ContainsKey(15) && leftHand != null)
            {
                Vector3 dir = (mpPoints[15] - mpPoints[13]).normalized;
                leftHand.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(12) && mpPoints.ContainsKey(14) && rightUpperArm != null)
            {
                Vector3 dir = (mpPoints[14] - mpPoints[12]).normalized;
                rightUpperArm.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(14) && mpPoints.ContainsKey(16) && rightLowerArm != null)
            {
                Vector3 dir = (mpPoints[16] - mpPoints[14]).normalized;
                rightLowerArm.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            // 用旋转驱动手掌
            if (mpPoints.ContainsKey(14) && mpPoints.ContainsKey(16) && rightHand != null)
            {
                Vector3 dir = (mpPoints[16] - mpPoints[14]).normalized;
                rightHand.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }

            // 3. 腿部旋转
            if (mpPoints.ContainsKey(23) && mpPoints.ContainsKey(25) && leftUpperLeg != null)
            {
                Vector3 dir = (mpPoints[25] - mpPoints[23]).normalized;
                leftUpperLeg.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(25) && mpPoints.ContainsKey(27) && leftLowerLeg != null)
            {
                Vector3 dir = (mpPoints[27] - mpPoints[25]).normalized;
                leftLowerLeg.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            // 用旋转驱动脚
            if (mpPoints.ContainsKey(25) && mpPoints.ContainsKey(27) && leftFoot != null)
            {
                Vector3 dir = (mpPoints[27] - mpPoints[25]).normalized;
                leftFoot.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(24) && mpPoints.ContainsKey(26) && rightUpperLeg != null)
            {
                Vector3 dir = (mpPoints[26] - mpPoints[24]).normalized;
                rightUpperLeg.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            if (mpPoints.ContainsKey(26) && mpPoints.ContainsKey(28) && rightLowerLeg != null)
            {
                Vector3 dir = (mpPoints[28] - mpPoints[26]).normalized;
                rightLowerLeg.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
            // 用旋转驱动脚
            if (mpPoints.ContainsKey(26) && mpPoints.ContainsKey(28) && rightFoot != null)
            {
                Vector3 dir = (mpPoints[28] - mpPoints[26]).normalized;
                rightFoot.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }

            // 4. 头部朝向（鼻子指向肩膀中点）
            if (mpPoints.ContainsKey(0) && mpPoints.ContainsKey(11) && mpPoints.ContainsKey(12) && head != null)
            {
                Vector3 shouldersMid = (mpPoints[11] + mpPoints[12]) / 2f;
                Vector3 dir = (mpPoints[0] - shouldersMid).normalized;
                head.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }
        }
        catch (System.Exception ex)
        {
            Debug.LogError("解析Mediapipe JSON失败: " + ex.Message);
        }
    }
} 