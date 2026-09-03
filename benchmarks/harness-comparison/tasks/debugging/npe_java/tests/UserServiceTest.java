import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

import java.util.Optional;

class UserServiceTest {

    private UserService service;

    @BeforeEach
    void setUp() {
        service = new UserService();
        service.addUser(new User("Alice", "alice@test.com",
            new Address("123 Main St", "New York", "10001")));
        service.addUser(new User("Bob", null,
            new Address("456 Oak Ave", null, "90210")));
        service.addUser(new User("Charlie", "charlie@test.com", null));
    }

    @Test
    void testFindUserPresent() {
        Optional<User> user = service.findUser("Alice");
        assertTrue(user.isPresent());
        assertEquals("Alice", user.get().getName());
    }

    @Test
    void testFindUserEmpty() {
        Optional<User> user = service.findUser("NonExistent");
        assertTrue(user.isEmpty());
    }

    @Test
    void testGetUserEmailPresent() {
        Optional<String> email = service.getUserEmail("Alice");
        assertTrue(email.isPresent());
        assertEquals("alice@test.com", email.get());
    }

    @Test
    void testGetUserEmailEmptyForNullEmail() {
        Optional<String> email = service.getUserEmail("Bob");
        assertTrue(email.isEmpty());
    }

    @Test
    void testGetUserEmailEmptyForMissingUser() {
        Optional<String> email = service.getUserEmail("NonExistent");
        assertTrue(email.isEmpty());
    }

    @Test
    void testGetUserCityPresent() {
        Optional<String> city = service.getUserCity("Alice");
        assertTrue(city.isPresent());
        assertEquals("New York", city.get());
    }

    @Test
    void testGetUserCityEmptyForNullCity() {
        Optional<String> city = service.getUserCity("Bob");
        assertTrue(city.isEmpty());
    }

    @Test
    void testGetUserCityEmptyForNullAddress() {
        Optional<String> city = service.getUserCity("Charlie");
        assertTrue(city.isEmpty());
    }

    @Test
    void testGetUserCityEmptyForMissingUser() {
        Optional<String> city = service.getUserCity("NonExistent");
        assertTrue(city.isEmpty());
    }

    @Test
    void testFormatUserInfoComplete() {
        String info = service.formatUserInfo("Alice");
        assertEquals("Alice (alice@test.com) from New York", info);
    }

    @Test
    void testFormatUserInfoMissingEmail() {
        String info = service.formatUserInfo("Bob");
        assertEquals("Bob (N/A) from Unknown", info);
    }

    @Test
    void testFormatUserInfoMissingAddress() {
        String info = service.formatUserInfo("Charlie");
        assertEquals("Charlie (charlie@test.com) from Unknown", info);
    }

    @Test
    void testFormatUserInfoMissingUser() {
        String info = service.formatUserInfo("NonExistent");
        assertEquals("NonExistent (N/A) from Unknown", info);
    }
}
