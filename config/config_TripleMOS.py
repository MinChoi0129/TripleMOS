def get_config():
    class General:
        log_frequency = 100
        name = __name__.rsplit("/")[-1].rsplit(".")[-1]
        batch_size_per_gpu = 5
        fp16 = False

        SeqDir = "/home/workspace/KITTI/dataset/sequences"
        category_list = ["static", "moving"]

        loss_mode = "ohem"
        K = 2

        class Voxel:
            # Cart-BEV
            cart_bev_shape = (512, 512, 30)
            cart_bev_range_x = (-50.0, 50.0)
            cart_bev_range_y = (-50.0, 50.0)
            cart_bev_range_z = (-4.0, 2.0)

            # Polar-BEV
            polar_bev_shape = (512, 512, 30)
            polar_bev_range_r = (2, 50)
            polar_bev_range_theta = (-180, 180)
            polar_bev_range_z = (-4.0, 2.0)

    class DatasetParam:
        class Train:
            data_src = "data_TripleMOS"
            num_workers = 4
            frame_point_num = 160000
            SeqDir = General.SeqDir
            Voxel = General.Voxel
            seq_num = General.K + 1

            class CopyPasteAug:
                is_use = True
                ObjBackDir = "/home/workspace/KITTI/object_bank_semkitti"
                paste_max_obj_num = 20

            class AugParam:
                noise_mean = 0
                noise_std = 0.0001
                theta_range = (-180.0, 180.0)
                shift_range = ((-3, 3), (-3, 3), (-0.4, 0.4))
                size_range = (0.95, 1.05)

        class Val:
            data_src = "data_TripleMOS"
            num_workers = 2
            frame_point_num = 160000
            SeqDir = General.SeqDir
            Voxel = General.Voxel
            seq_num = General.K + 1

    class ModelParam:
        prefix = "TripleMOS.AttNet"
        Voxel = General.Voxel
        category_list = General.category_list
        class_num = len(category_list) + 1
        loss_mode = General.loss_mode
        seq_num = General.K + 1
        fusion_mode = "CatFusion"
        point_feat_out_channels = 64

        class BEVParam:
            base_block = "BasicBlock"
            context_layers = [64, 32, 64, 128]
            layers = [2, 3, 4]
            bev_grid2point = dict(type="BilinearSample", scale_rate=(0.5, 0.5))

        class RVParam:
            base_block = "BasicBlock"
            context_layers = [64, 32, 64, 128]
            layers = [2, 3, 4]
            rv_grid2point = dict(type="BilinearSample", scale_rate=(1.0, 0.5))

        class pretrain:  # 학습 이어서 할 때 여기 keep_training, Epoch 설정
            pretrain_epoch = 3  # 이 숫자까지 학습했다고 가정함. 즉 +1 한 Epoch을 이어서 시작할 것임.

    class OptimizeParam:
        class optimizer:
            type = "sgd"
            base_lr = 0.02
            momentum = 0.9
            nesterov = True
            wd = 1e-3

        class schedule:
            type = "step"
            begin_epoch = 0
            end_epoch = 100
            pct_start = 0.01
            final_lr = 1e-6
            step = 3
            decay_factor = 0.5

    return General, DatasetParam, ModelParam, OptimizeParam
