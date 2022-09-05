from proto.action_pb2 import ActionType, Action, Report

if __name__ == '__main__':
    rep = Report()
    rep.report = "Hello World!"
    action = Action()
    action.type = ActionType.ACTION_INITIATE
    action.from_id = 2
    action.to_id = 3
    action.report.MergeFrom(rep)

    print(str(action))

