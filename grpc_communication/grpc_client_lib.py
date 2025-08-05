import grpc
import threading
import queue
import time
from typing import Callable, Optional

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入生成的protobuf和grpc模块
from grpc_communication import data_pb2
from grpc_communication import data_pb2_grpc
from grpc_communication import data_act_pb2
from grpc_communication import data_act_pb2_grpc

class GRPCClientBase:
    """gRPC客户端基类，封装通用功能"""
    def __init__(self, server_address: str):
        self.server_address = server_address
        self.channel = None
        self.stub = None
        self.response_queue = queue.Queue()  # 接收消息队列
        self.request_queue = queue.Queue()   # 发送消息队列
        self.is_running = False
        self.receive_thread = None
        self.chat_stream = None
        self.message_callback = None  # 消息回调函数

    def connect(self) -> bool:
        """建立连接"""
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            # 检查连接状态
            if not self._wait_for_channel_ready(timeout=5):
                return False
            self.is_running = True
            self._start_streams()
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False

    def _wait_for_channel_ready(self, timeout: int = 5) -> bool:
        """等待通道就绪"""
        try:
            grpc.channel_ready_future(self.channel).result(timeout=timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    def _start_streams(self):
        """启动流和接收线程，由子类实现"""
        raise NotImplementedError("子类必须实现此方法")

    def send_message(self, message: str) -> bool:
        """发送消息到服务器"""
        if not self.is_running:
            return False
        try:
            self.request_queue.put(message)
            return True
        except Exception as e:
            print(f"发送消息失败: {str(e)}")
            return False

    def set_message_callback(self, callback: Callable[[str], None]):
        """设置消息接收回调函数"""
        self.message_callback = callback

    def get_received_message(self, timeout: float = None) -> Optional[str]:
        """从队列获取接收到的消息"""
        try:
            n_try = 1145 
            while((len(self.response_queue.queue)==0) and n_try>0):
                time.sleep(0.01)
                n_try = n_try-1
                
            # 改成了 response queue
            jieguo = self.response_queue.get(block=True,timeout=timeout)
            return jieguo
        except queue.Empty:
            return None

    def stop(self):
        """停止客户端"""
        self.is_running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        if self.channel:
            self.channel.close()
        self.channel = None
        self.stub = None
        self.chat_stream = None

    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop()


class DataActClient(GRPCClientBase):
    """基于data_act.proto的客户端"""
    def _start_streams(self):
        # 创建stub
        self.stub = data_act_pb2_grpc.BidirectionalServiceACTStub(self.channel)
        # 创建聊天流
        self.chat_stream = self.stub.Chat(self._generate_requests())
        # 启动接收线程
        self.receive_thread = threading.Thread(target=self._receive_responses)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _generate_requests(self):
        """生成请求流"""
        while self.is_running:
            try:
                message = self.request_queue.get(block=True,timeout=0.1)
                request = data_act_pb2.StringMessageACT(data=message)
                yield request
                self.request_queue.task_done()
                time.sleep(0.01)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"生成请求错误: {e}")
                break

    def _receive_responses(self):
        """接收服务器响应"""
        try:
            for response in self.chat_stream:
                message = response.data
                self.response_queue.put(message)
                # 如果设置了回调函数，调用它
                if self.message_callback:
                    self.message_callback(message)
                if not self.is_running:
                    break
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code == grpc.StatusCode.CANCELLED:
                print("流已被取消")
            else:
                print(f"RPC错误: {e.details()}")
        except Exception as e:
            print(f"接收响应错误: {e}")
        finally:
            self.is_running = False


class DataClient(GRPCClientBase):
    """基于data.proto的客户端"""
    def _start_streams(self):
        # 创建stub
        self.stub = data_pb2_grpc.BidirectionalServiceStub(self.channel)
        # 创建聊天流
        self.chat_stream = self.stub.Chat(self._generate_requests())
        # 启动接收线程
        self.receive_thread = threading.Thread(target=self._receive_responses)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _generate_requests(self):
        """生成请求流"""
        while self.is_running:
            try:
                message = self.request_queue.get(block=True, timeout=0.1)
                request = data_pb2.StringMessage(data=message)
                yield request
                self.request_queue.task_done()
                time.sleep(0.01)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"生成请求错误: {e}")
                break

    def _receive_responses(self):
        """接收服务器响应"""
        try:
            for response in self.chat_stream:
                message = response.data
                self.response_queue.put(message)
                # 如果设置了回调函数，调用它
                if self.message_callback:
                    self.message_callback(message)
                if not self.is_running:
                    break
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code == grpc.StatusCode.CANCELLED:
                print("流已被取消")
            else:
                print(f"RPC错误: {e.details()}")
        except Exception as e:
            print(f"接收响应错误: {e}")
        finally:
            self.is_running = False


class GRPCClientManager:
    """gRPC客户端管理器，用于管理多个客户端实例"""
    def __init__(self):
        self.clients = []

    def create_data_act_client(self, server_address: str) -> DataActClient:
        """创建基于data_act.proto的客户端"""
        client = DataActClient(server_address)
        self.clients.append(client)
        return client

    def create_data_client(self, server_address: str) -> DataClient:
        """创建基于data.proto的客户端"""
        client = DataClient(server_address)
        self.clients.append(client)
        return client

    def shutdown_all(self):
        """关闭所有客户端连接"""
        for client in self.clients:
            client.stop()
        self.clients.clear()