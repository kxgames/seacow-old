import kxg
import tokens

class WelcomeClient (object):
    def __init__(self, name):
        from string import capwords
        self.name = capwords(name)

class StartGame (kxg.Message):

    def check(self, world, sender):
        return not world.has_game_started()

    def execute(self, world):
        world.start_game()

    def notify(self, actor, sent_from_here):
        actor.start_game()


class GameOver (kxg.Message):

    def __init__(self, winner):
        self.winner = winner

    def check(self, world, sender):
        return sender == 'referee'

    def execute(self, world):
        world.game_over(self.winner)

    def notify(self, actor, sent_from_here):
        actor.game_over(self.winner)



class CreatePlayer (kxg.Greeting):

    def __init__(self, name, color):
        self.player = tokens.Player(name, color)

    def get_sender(self):
        return self.player

    def check(self, world, sender):
        return not world.has_game_started()

    def setup(self, world, sender, id):
        self.player.give_id(id)

    def execute(self, world):
        world.create_player(self.player)

    def notify(self, actor, is_mine):
        actor.create_player(self.player, is_mine)


class CreateCity (kxg.Message):

    def __init__(self, player, position):
        self.city = tokens.City(player, position)
        self.price = self.city.get_price()

    def check(self, world, sender):
        city = self.city
        self.price = self.city.get_price()
        player = city.player

        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "City requested by wrong player."
            return False

        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't build cities."
            return False

        # Make sure the player can afford this city.
        if not player.can_afford_price(self.price):
            self.error = "Can't afford $%d for a new city." % self.price
            return False

        # Make sure this city can be placed here.
        if not player.can_place_city(city):
            self.error = "Can't place a city in that location."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        self.city.give_id(id)

    def execute(self, world):
        world.create_city(self.city, self.price)

    def notify(self, actor, is_mine):
        actor.create_city(self.city, is_mine)


class CreateArmy (kxg.Message):

    def __init__(self, player, position):
        self.army = tokens.Army(player, position)
        self.price = self.army.get_price()

    def check(self, world, sender):
        army = self.army
        self.price = self.army.get_price()
        player = army.player

        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Army requested by wrong player."
            return False

        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't build armies."
            return False

        # Make sure the player can afford this army.
        if not player.can_afford_price(self.price):
            self.error = "Can't afford $%d for a new army." % self.price
            return False

        # Make sure this army can be placed here.
        if not player.can_place_army(army):
            self.error = "Can't place an army in that location."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        self.army.give_id(id)

    def execute(self, world):
        world.create_army(self.army, self.price)

    def notify(self, actor, is_mine):
        actor.create_army(self.army, is_mine)


class CreateRoad (kxg.Message):

    def __init__(self, player, start, end):
        self.road = tokens.Road(player, start, end)
        self.price = self.road.get_price()

    def check(self, world, sender):
        road = self.road; price = self.price
        player = road.player; start = road.start; end = road.end

        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Road requested by wrong player."
            return False

        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't build roads."
            return False

        # Make sure the right player owns the cities being connected.
        if (player is not start.player) or (player is not end.player):
            self.error = "Can't build roads to enemy cities."
            return False

        # Make sure the player can afford this road.
        if not player.can_afford_price(price):
            self.error = "Can't afford $%d for a new road." % price
            return False

        # Make sure this road doesn't already exist.
        for other in player.roads:
            if road.has_same_route(other):
                self.error = "Can't make two roads between the same cities."
                return False

        # Make sure neither end of the road is under battle.
        if start.is_in_battle() or end.is_in_battle():
            self.error = "Can't build a road to a city under battle."
            return False

        # Make sure there are no obstacles in the way of this road.
        if not player.can_place_road(road):
            self.error = "Can't build a road through an existing city."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        self.road.give_id(id)

    def execute(self, world):
        world.create_road(self.road, self.price)

    def notify(self, actor, is_mine):
        actor.create_road(self.road, is_mine)



class UpgradeCommunity (kxg.Message):

    def __init__(self, community):
        self.community = community

    def check(self, world, sender):
        community = self.community
        player = community.player
        price = self.community.get_upgrade_price()
        
        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Upgrade requested by wrong player."
            return False

        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't upgrade cities."
            return False

        # Make sure the community in question is not in a battle.
        if community.is_in_battle():
            self.error = "Can't upgrade a community that's engaged in a battle."
            return False

        # Make sure the player can afford to upgrade the community.
        if not player.can_afford_price(price):
            self.error = "Can't afford $%d to upgrade this community." % price
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def execute(self, world):
        world.upgrade_community(self.community, self.community.get_upgrade_price())

    def notify(self, actor, is_mine):
        actor.upgrade_community(self.community, is_mine)


class DestroyArmy (kxg.Message):
    
    def __init__(self, army):
        self.army = army

    def check(self, world, sender):
        army = self.army
        
        # Make sure the city is actually an city.
        if not isinstance(army, tokens.Army):
            self.error = "Community must be an army."
            return False

        # Make sure the city is at 0 health.
        if not army.get_health() <= 0:
            self.error = "Army must be at zero health to be destroyed."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        print "Destroying army %s" %(self.army.get_id())

    def execute(self, world):
        world.destroy_army(self.army)

    def notify(self, actor, is_mine):
        actor.destroy_army(self.army, is_mine)



class RequestBattle (kxg.Message):

    def __init__(self, army, community):
        self.campaign = tokens.Campaign(army, community)

    def check(self, world, sender):
        army = self.campaign.army
        community = self.campaign.community
        player = army.player
        price = community.get_battle_price()

        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Battle requested by wrong player."
            return False

        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't request battles."
            return False

        # Make sure the army is not attacking one of its own.
        if community.player is player:
            self.error = "Army can't attack friendly community."
            return False
        
        # Make sure the army is not already in a battle.
        if army.battle:
            self.error = "Army can't start a new battle while it is already in one."
            return False

        # Make sure the army can move to the end point.
        if not army.can_request_battle(community):
            self.error = "Army can't move there."
            return False
        
        # Make sure the player can afford to battle community.
        if not player.can_afford_price(price):
            self.error = "Can't afford $%d to battle this community." % price
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup (self, world, sender, id):
        self.campaign.give_id(id)
        print "RequestBattle: Campaign %s" %self.campaign.get_id()
        print "    Army %s chasing Community %s" %(self.campaign.army.get_id(), self.campaign.community.get_id())

    def execute(self, world):
        world.request_battle(self.campaign)

    def notify(self, actor, is_mine):
        actor.request_battle(self.campaign, is_mine)


class StartBattle (kxg.Message):

    def __init__(self, campaign):
        self.campaign = campaign
        self.battle = tokens.Battle(campaign)

    def check(self, world, sender):
        army = self.campaign.army
        target = self.campaign.community
        
        # Make sure the army is not attacking one of its own.
        if target.player is army.player:
            self.error = "Army can't attack friendly targets."
            return False
        
        # Make sure the army is not already in a battle.
        if army.battle:
            self.error = "Army can't start a new battle while it is already in one."
            return False
        
        # Make sure the target is not already in a battle.
        # Use JoinBattle if they are.
        if target.battle:
            self.error = "Army can't start a new battle with the target."
            return False

        # Check proximity to the target.
        if not army.check_engagement_proximity(target):
            self.error = "Army must be close to the target to start battle."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        self.battle.give_id(id)
        print "StartBattle  %s (Campaign %s completed!)" %(self.battle.get_id(), self.campaign.get_id())
        print "    Battle %s communities: %s, %s" %(self.battle.get_id(), self.campaign.army.get_id(), self.campaign.community.get_id())

    def execute(self, world):
        world.start_battle(self.campaign, self.battle)

    def notify(self, actor, sent_from_here):
        actor.start_battle(self.battle)


class JoinBattle (kxg.Message):

    def __init__(self, campaign, battle):
        self.campaign = campaign
        self.battle = battle

    def check(self, world, sender):
        army = self.campaign.army
        community = self.campaign.community
        
        ## If the community is friendly, then the army is coming to it's aid.  
        ## No need to check ownership.
        
        # Make sure the army is not already in a battle.
        if army.battle:
            self.error = "Army can't start a new battle while it is already in one."
            return False
        
        # Make sure the target is in a battle.
        # Use StartBattle if they aren't.
        if not community.battle:
            self.error = "Target must be in a battle for the army to join."
            return False

        # Check proximity to the battle.
        if not army.check_battle_proximity(community.battle):
            self.error = "Army must be close to an enemy target to join a battle."
            return False

        return True

    def reject(self, actor):
        print self.error
        actor.show_error(self)

    def setup(self, world, sender, id):
        print "JoinBattle %s (Campaign %s completed!)" %(self.battle.get_id(), self.campaign.get_id())
        msg = ""
        for coms in self.battle.communities.values():
            for com in coms:
                msg += "%d, " % com.get_id()
        print "    Battle %s communities: %s%s" %(self.battle.get_id(), msg, self.campaign.army.get_id())

    def execute(self, world):
        world.join_battle(self.campaign, self.battle)

    def notify(self, actor, sent_from_here):
        actor.join_battle(self.battle)


class RetreatBattle (kxg.Message):
    
    def __init__(self, army, target):
        self.army = army
        self.target = target
        self.battle = army.battle

    def check(self, world, sender):
        army = self.army
        target = self.target
        player = army.player
        
        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Retreat requested by wrong player."
            return False

        # Make sure the army is actually an army.
        if not isinstance(army, tokens.Army):
            self.error = "Only armies can retreat."
            return False

        # Make sure the army is in a battle or campaign.
        if not army.battle and not army.my_campaign:
            self.error = "Army must be in a battle or campaign to retreat."
            return False

        # Make sure the army can move to the end point.
        if not army.can_move_to(target):
            self.error = "Army can't move there."
            return False
        
        self.price = army.battle.get_retreat_battle_price()
        
        # Make sure the player can afford to retreat.
        if not player.can_afford_price(self.price):
            self.error = "Can't afford $%d to retreat from battle." % self.price
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        print "RetreatBattle  %s  Army %s" %(self.battle.get_id(), self.army.get_id())

    def execute(self, world):
        world.retreat_battle(self.army, self.target)

    def notify(self, actor, is_mine):
        actor.retreat_battle(self.army, self.target, is_mine)


class ZombifyCity (kxg.Message):
    
    def __init__(self, city):
        self.city = city
        self.battle = city.battle

    def check(self, world, sender):
        city = self.city
        
        # Make sure the city is actually an city.
        if not isinstance(city, tokens.City):
            self.error = "Only cities can be zombified."
            return False

        # Make sure the city is in a battle.
        if not city.battle:
            self.error = "City must be in a battle to be zombified."
            return False
        
        # Make sure the city is at 0 health.
        if not city.get_health() <= 0:
            self.error = "City must be at zero health to be zombified."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        print "zombifying city %s  in battle %s" %(self.city.get_id(), self.battle.get_id())

    def execute(self, world):
        world.zombify_city(self.city.battle, self.city)

    def notify(self, actor, is_mine):
        actor.zombify_city(self.city.battle, self.city, is_mine)


class EndBattle (kxg.Message):
    
    def __init__(self, battle):
        self.battle = battle

    def check(self, world, sender):
        
        # Make sure the battle is actually over.
        if not self.battle.was_successful():
            self.error = "Can't end the battle, battle is still in progress."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def setup(self, world, sender, id):
        print "Battle %s ended" %self.battle.get_id()

    def execute(self, world):
        world.end_battle(self.battle)

    def notify(self, actor, is_mine):
        actor.end_battle(self.battle, is_mine)



class old_CaptureCity (kxg.Message):

    def __init__(self, battle):
        self.battle = battle

    def check(self, world, sender):
        return self.battle.was_successful()

    def execute(self, world):
        world.capture_city(self.battle)

    def notify(self, actor, sent_from_here):
        actor.capture_city(self.battle)


class DefeatPlayer (kxg.Message):

    def __init__(self, player):
        self.player = player

    def check(self, world, sender):
        return self.player.was_defeated() and not self.player.is_dead()

    def setup(self, world, sender, id):
        print "Player %s defeated" %self.player.get_id()

    def execute(self, world):
        world.defeat_player(self.player)

    def notify(self, actor, sent_from_here):
        actor.defeat_player()



class MoveArmy (kxg.Message):

    def __init__(self, army, end_point):
        self.army = army
        self.target = end_point

    def check(self, world, sender):
        army = self.army
        target = self.target
        player = army.player

        # Make sure the right player is sending this message.
        if sender is not player:
            self.error = "Army motion requested by wrong player."
            return False
        #
        # Make sure the player is still alive.
        if player.was_defeated():
            self.error = "Defeated players can't move armies."
            return False

        # Make sure the army is not already in a battle.
        if army.battle:
            self.error = "Army can't move when it is in a battle."
            return False

        # Make sure the army can move to the end point.
        if not army.can_move_to(target):
            self.error = "Army can't move there."
            return False

        return True

    def reject(self, actor):
        actor.show_error(self)

    def execute(self, world):
        self.army.move_to(self.target)

    def notify(self, actor, is_mine):
        actor.move_army(self.army, self.target, is_mine)


