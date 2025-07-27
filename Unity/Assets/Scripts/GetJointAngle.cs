using UnityEngine;
using BioIK;
using UnityEngine.XR;
using System.Collections.Generic;

public class GetJointAngle : MonoBehaviour
{
    private BioIK.BioIK bioIKController;  // BioIK组件引用
    public BioIK.BioIK neckBioIKController;  // Neck-H1的BioIK组件引用

    // 左手骨骼引用
    public Transform leftBone1;
    public Transform leftBone2;
    public Transform leftBone3;
    public Transform leftBone4;
    public Transform leftBone5;
    public Transform leftBone6;
    public Transform leftBone7;

    // 右手骨骼引用
    public Transform rightBone9;
    public Transform rightBone10;
    public Transform rightBone11;
    public Transform rightBone12;
    public Transform rightBone13;
    public Transform rightBone14;
    public Transform rightBone15;

    // 左手关节角度翻转设置
    public bool leftJoint1Invert = false;
    public bool leftJoint2Invert = false;
    public bool leftJoint3Invert = false;
    public bool leftJoint4Invert = false;
    public bool leftJoint5Invert = false;
    public bool leftJoint6Invert = false;
    public bool leftJoint7Invert = false;
    public bool leftTriggerInvert = false;

    // 右手关节角度翻转设置
    public bool rightJoint9Invert = false;
    public bool rightJoint10Invert = false;
    public bool rightJoint11Invert = false;
    public bool rightJoint12Invert = false;
    public bool rightJoint13Invert = false;
    public bool rightJoint14Invert = false;
    public bool rightJoint15Invert = false;
    public bool rightTriggerInvert = false;

    // 左手关节
    private BioIK.BioSegment leftJoint1;
    private BioIK.BioSegment leftJoint2;
    private BioIK.BioSegment leftJoint3;
    private BioIK.BioSegment leftJoint4;
    private BioIK.BioSegment leftJoint5;
    private BioIK.BioSegment leftJoint6;
    private BioIK.BioSegment leftJoint7;
    private BioIK.BioSegment leftJoint8;

    // 右手关节
    private BioIK.BioSegment rightJoint9;
    private BioIK.BioSegment rightJoint10;
    private BioIK.BioSegment rightJoint11;
    private BioIK.BioSegment rightJoint12;
    private BioIK.BioSegment rightJoint13;
    private BioIK.BioSegment rightJoint14;
    private BioIK.BioSegment rightJoint15;
    private BioIK.BioSegment rightJoint16;

    private InputDevice leftController;
    private InputDevice rightController;

    void Start()
    {
        // 获取BioIK组件
        bioIKController = GetComponent<BioIK.BioIK>();

        InitializeControllers();

        // 初始化左手关节
        leftJoint1 = bioIKController.FindSegment(leftBone1);
        leftJoint2 = bioIKController.FindSegment(leftBone2);
        leftJoint3 = bioIKController.FindSegment(leftBone3);
        leftJoint4 = bioIKController.FindSegment(leftBone4);
        leftJoint5 = bioIKController.FindSegment(leftBone5);
        leftJoint6 = bioIKController.FindSegment(leftBone6);
        leftJoint7 = bioIKController.FindSegment(leftBone7);

        // 初始化右手关节
        rightJoint9 = bioIKController.FindSegment(rightBone9);
        rightJoint10 = bioIKController.FindSegment(rightBone10);
        rightJoint11 = bioIKController.FindSegment(rightBone11);
        rightJoint12 = bioIKController.FindSegment(rightBone12);
        rightJoint13 = bioIKController.FindSegment(rightBone13);
        rightJoint14 = bioIKController.FindSegment(rightBone14);
        rightJoint15 = bioIKController.FindSegment(rightBone15);
    }

    private void InitializeControllers()
    {
        List<InputDevice> leftHandDevices = new List<InputDevice>();
        List<InputDevice> rightHandDevices = new List<InputDevice>();
        
        InputDevices.GetDevicesWithCharacteristics(
            InputDeviceCharacteristics.Left | InputDeviceCharacteristics.Controller, 
            leftHandDevices);
        
        InputDevices.GetDevicesWithCharacteristics(
            InputDeviceCharacteristics.Right | InputDeviceCharacteristics.Controller, 
            rightHandDevices);
        
        if (leftHandDevices.Count > 0)
        {
            leftController = leftHandDevices[0];
        }
        
        if (rightHandDevices.Count > 0)
        {
            rightController = rightHandDevices[0];
        }
    }

    private void Update()
    {
        // 检查左手控制器
        if (!leftController.isValid)
        {
            InitializeControllers();
        }
        
        // 检查右手控制器
        if (!rightController.isValid)
        {
            InitializeControllers();
        }
    }

    private float GetTriggerValue(InputDevice controller)
    {
        float triggerValue = 0f;
        if (controller.isValid)
        {
            // 读取扳机键值
            if (controller.TryGetFeatureValue(CommonUsages.trigger, out triggerValue))
            {
                // 将扳机键的值(0-1)转换为(0-100)
                return triggerValue * 100f;
            }
        }
        return 0f;
    }

    // 获取关节角度（弧度转换为角度）
    private float GetJointAngleValue(BioIK.BioSegment joint)
    {
        if (joint == null || joint.Joint == null) return 0f;
        
        float angleX = (float)joint.Joint.X.GetTargetValue(true);
        float angleY = (float)joint.Joint.Y.GetTargetValue(true);
        float angleZ = (float)joint.Joint.Z.GetTargetValue(true);

        float angle = angleZ;
        return angle * Mathf.Rad2Deg;
    }

    // 获取左手关节角度数组
    public void GetLeftHandAnglesArray(float[] angles, int startIndex)
    {
        angles[startIndex + 0] = GetJointAngleValue(leftJoint1) * (leftJoint1Invert ? -1 : 1);
        angles[startIndex + 1] = GetJointAngleValue(leftJoint2) * (leftJoint2Invert ? -1 : 1);
        angles[startIndex + 2] = GetJointAngleValue(leftJoint3) * (leftJoint3Invert ? -1 : 1);
        angles[startIndex + 3] = GetJointAngleValue(leftJoint4) * (leftJoint4Invert ? -1 : 1);
        angles[startIndex + 4] = GetJointAngleValue(leftJoint5) * (leftJoint5Invert ? -1 : 1);
        angles[startIndex + 5] = GetJointAngleValue(leftJoint6) * (leftJoint6Invert ? -1 : 1);
        angles[startIndex + 6] = GetJointAngleValue(leftJoint7) * (leftJoint7Invert ? -1 : 1);
        angles[startIndex + 7] = (100-GetTriggerValue(leftController)) * (leftTriggerInvert ? -1 : 1);
    }

    // 获取右手关节角度数组
    public void GetRightHandAnglesArray(float[] angles, int startIndex)
    {
        angles[startIndex + 0] = GetJointAngleValue(rightJoint9) * (rightJoint9Invert ? -1 : 1);
        angles[startIndex + 1] = GetJointAngleValue(rightJoint10) * (rightJoint10Invert ? -1 : 1);
        angles[startIndex + 2] = GetJointAngleValue(rightJoint11) * (rightJoint11Invert ? -1 : 1);
        angles[startIndex + 3] = GetJointAngleValue(rightJoint12) * (rightJoint12Invert ? -1 : 1);
        angles[startIndex + 4] = GetJointAngleValue(rightJoint13) * (rightJoint13Invert ? -1 : 1);
        angles[startIndex + 5] = GetJointAngleValue(rightJoint14) * (rightJoint14Invert ? -1 : 1);
        angles[startIndex + 6] = GetJointAngleValue(rightJoint15) * (rightJoint15Invert ? -1 : 1);
        angles[startIndex + 7] = (100-GetTriggerValue(rightController)) * (rightTriggerInvert ? -1 : 1);
    }


    // 获取左手关节角度字符串
    public string GetLeftHandAngles()
    {
        float[] angles = new float[8];
        GetLeftHandAnglesArray(angles, 0);
        return string.Join(",", angles);
    }

    // 获取右手关节角度字符串
    public string GetRightHandAngles()
    {
        float[] angles = new float[8];
        GetRightHandAnglesArray(angles, 0);
        return string.Join(",", angles);
    }
}
